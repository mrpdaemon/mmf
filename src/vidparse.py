#!/usr/bin/python

import subprocess, re

class VidParser:
    """Video file parser class using mediainfo"""
    def __init__(self, inputFileName):
        self.inputFileName = inputFileName
        video_section = False
        
        mp = subprocess.Popen(['mediainfo', "".join(inputFileName)], stdout=subprocess.PIPE)
        mp_output = mp.communicate()
        
        mp_tokenized = mp_output[0].split("\n")
        for mp_line in mp_tokenized:
            if mp_line == "Video":
                video_section = True
            if (mp_line == "Audio") or (mp_line == "Audio #1"):
                video_section = False
            if video_section == True:
                if  "Format  " in mp_line:
                    splitter = re.compile(r'[:]+')
                    mp_line_tokenized = splitter.split(mp_line)
                    self.vid_format = mp_line_tokenized[len(mp_line_tokenized) - 1][1:]
                if  "Codec ID " in mp_line:
                    splitter = re.compile(r'[:]+')
                    mp_line_tokenized = splitter.split(mp_line)
                    self.vid_codec_id = mp_line_tokenized[len(mp_line_tokenized) - 1][1:]
                if "Scan type " in mp_line:
                    splitter = re.compile(r'[:]+')
                    mp_line_tokenized = splitter.split(mp_line)
                    self.vid_scan = mp_line_tokenized[len(mp_line_tokenized) - 1][1:]
                if "Width " in mp_line:
                    splitter = re.compile(r'[:]+')
                    mp_line_tokenized = splitter.split(mp_line)
                    vid_width_str = mp_line_tokenized[len(mp_line_tokenized) - 1][1:]
                    splitter = re.compile(r'[ ]+')
                    vid_width_str_tokenized = splitter.split(vid_width_str)
                    if len(vid_width_str_tokenized) == 3: # need to combine first 2
                        self.vid_width = vid_width_str_tokenized[0] + vid_width_str_tokenized[1]
                    else:
                        self.vid_width = vid_width_str_tokenized[0]
                if "Height " in mp_line:
                    splitter = re.compile(r'[:]+')
                    mp_line_tokenized = splitter.split(mp_line)
                    vid_height_str = mp_line_tokenized[len(mp_line_tokenized) - 1][1:]
                    splitter = re.compile(r'[ ]+')
                    vid_height_str_tokenized = splitter.split(vid_height_str)
                    if len(vid_height_str_tokenized) == 3: # need to combine first 2
                        self.vid_height = vid_height_str_tokenized[0] + vid_height_str_tokenized[1]
                    else:
                        self.vid_height = vid_height_str_tokenized[0]
        
    def __repr__(self):
        retStr = "\nInput file: "+ self.inputFileName + "\n\n"
        retStr += "Video:\n"
        retStr += ("\tFormat: " + self.vid_format + "\n")
        retStr += ("\tCodec ID: "+ self.vid_codec_id + "\n")
        retStr += ("\tScan type: " + self.vid_scan + "\n")
        retStr += ("\tWidth: " + self.vid_width + "\n")
        retStr += ("\tHeight: " + self.vid_height + "\n")
        return retStr

if __name__ == "__main__":
    import sys
    testParser = VidParser(sys.argv[1])
    print testParser