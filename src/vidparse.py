#!/usr/bin/python

import subprocess, re

class VidParser:
    """Video file parser class using mediainfo"""
    
    def get_field_value(self, lineStr):
        splitter = re.compile(r'[:]+')
        line_tokenized = splitter.split(lineStr)
        return line_tokenized[len(line_tokenized) - 1][1:]
        
    def __init__(self, inputFileName):
        INVALID_SECTION = 0
        VIDEO_SECTION = 1
        AUDIO_SECTION = 2
        TEXT_SECTION = 3
    
        self.inputFileName = inputFileName
        current_section = INVALID_SECTION
        
        mp = subprocess.Popen(['mediainfo', "".join(inputFileName)], stdout=subprocess.PIPE)
        mp_output = mp.communicate()
        
        mp_tokenized = mp_output[0].split("\n")
        for mp_line in mp_tokenized:
            if mp_line == "Video":
                current_section = VIDEO_SECTION
            elif (mp_line == "Audio") or (mp_line == "Audio #1"):
                current_section = AUDIO_SECTION
            elif (mp_line == "Text"):
                current_section = TEXT_SECTION
            elif current_section == VIDEO_SECTION:
                if  "Format  " in mp_line:
                    self.vid_format = self.get_field_value(mp_line)
                elif  "Codec ID " in mp_line:
                    self.vid_codec_id = self.get_field_value(mp_line)
                elif  "ID  " in mp_line:
                    # Codec ID check needs to be above stream ID check
                    self.vid_stream_id = self.get_field_value(mp_line)
                elif "Scan type " in mp_line:
                    self.vid_scan = self.get_field_value(mp_line)
                elif "Width " in mp_line:
                    vid_width_str = self.get_field_value(mp_line)
                    splitter = re.compile(r'[ ]+')
                    vid_width_str_tokenized = splitter.split(vid_width_str)
                    if len(vid_width_str_tokenized) == 3: # need to combine first 2
                        self.vid_width = vid_width_str_tokenized[0] + vid_width_str_tokenized[1]
                    else:
                        self.vid_width = vid_width_str_tokenized[0]
                elif "Height " in mp_line:
                    vid_height_str = self.get_field_value(mp_line)
                    splitter = re.compile(r'[ ]+')
                    vid_height_str_tokenized = splitter.split(vid_height_str)
                    if len(vid_height_str_tokenized) == 3: # need to combine first 2
                        self.vid_height = vid_height_str_tokenized[0] + vid_height_str_tokenized[1]
                    else:
                        self.vid_height = vid_height_str_tokenized[0]
            elif current_section == AUDIO_SECTION:
                if  "Format  " in mp_line:
                    self.audio_format = self.get_field_value(mp_line)
                if  "Codec ID " in mp_line:
                    self.audio_codec_id = self.get_field_value(mp_line)
                elif  "ID  " in mp_line:
                    # Codec ID check needs to be above stream ID check
                    self.audio_stream_id = self.get_field_value(mp_line)
                    continue
        
    def __repr__(self):
        retStr = "\nInput file: "+ self.inputFileName + "\n\n"
        retStr += "Video:\n"
        retStr += "\tStream ID: " + self.vid_stream_id + "\n"
        retStr += "\tFormat: " + self.vid_format + "\n"
        retStr += "\tCodec ID: "+ self.vid_codec_id + "\n"
        retStr += "\tScan type: " + self.vid_scan + "\n"
        retStr += "\tWidth: " + self.vid_width + "\n"
        retStr += "\tHeight: " + self.vid_height + "\n"
        retStr += "Audio:\n"
        retStr += "\tStream ID: " + self.audio_stream_id + "\n"
        retStr += "\tFormat: " + self.audio_format + "\n"
        retStr += "\tCodec ID: " + self.audio_codec_id + "\n"
        return retStr

if __name__ == "__main__":
    import sys
    testParser = VidParser(sys.argv[1])
    print testParser