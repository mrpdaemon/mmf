#!/usr/bin/python

import subprocess, re

def get_field_value(line_str):
    splitter = re.compile(r'[:]+')
    line_tokenized = splitter.split(line_str)
    return line_tokenized[len(line_tokenized) - 1][1:]

def field_collapse_thousands(field_str):
    result = []
    splitter = re.compile(r'[ ]+')
    field_str_tokenized = splitter.split(field_str)
    if len(field_str_tokenized) == 3: # need to combine first 2
        result.append(field_str_tokenized[0] + field_str_tokenized[1])
        result.append(field_str_tokenized[2])
    else:
        result.append(field_str_tokenized[0])
        result.append(field_str_tokenized[1])
    return result

def float_to_str_trunc(float_val):
    return str(round(float_val, 0))[:-2]

def bit_rate_convert(bit_rate_tokenized):
    if bit_rate_tokenized[1] == "Kbps":
        return float_to_str_trunc(float(bit_rate_tokenized[0]))
    elif bit_rate_tokenized[1] == "Mbps":
        return float_to_str_trunc(float(bit_rate_tokenized[0]) * 1024)
    else:
        raise Exception("Unknown bit rate string")
                 
class VidParser:
    """Video file parser class using mediainfo"""
    
    def __init__(self, input_file_name):
        INVALID_SECTION = 0
        VIDEO_SECTION = 1
        AUDIO_SECTION = 2
        TEXT_SECTION = 3
    
        self.input_file_name = input_file_name
        current_section = INVALID_SECTION
        
        mp = subprocess.Popen(['mediainfo', "".join(input_file_name)], stdout=subprocess.PIPE)
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
                    self.vid_format = get_field_value(mp_line)
                elif  "Codec ID " in mp_line:
                    self.vid_codec_id = get_field_value(mp_line)
                elif  "ID  " in mp_line:
                    # Codec ID check needs to be above stream ID check
                    self.vid_stream_id = int(get_field_value(mp_line))
                elif "Scan type " in mp_line:
                    self.vid_scan = get_field_value(mp_line)
                elif "Width " in mp_line:
                    vid_width_str = get_field_value(mp_line)
                    self.vid_width = int(field_collapse_thousands(vid_width_str)[0])
                elif "Height " in mp_line:
                    vid_height_str = get_field_value(mp_line)
                    self.vid_height = int(field_collapse_thousands(vid_height_str)[0])
                elif "Bit rate  " in mp_line:
                    vid_bit_rate_str = get_field_value(mp_line)
                    self.vid_bitrate = int(bit_rate_convert(field_collapse_thousands(vid_bit_rate_str)))
            elif current_section == AUDIO_SECTION:
                if  "Format  " in mp_line:
                    self.audio_format = get_field_value(mp_line)
                elif  "Codec ID " in mp_line:
                    self.audio_codec_id = get_field_value(mp_line)
                elif  "ID  " in mp_line:
                    # Codec ID check needs to be above stream ID check
                    self.audio_stream_id = int(get_field_value(mp_line))
                elif "Bit rate  " in mp_line:
                    audio_bit_rate_str = get_field_value(mp_line)
                    self.audio_bitrate = int(bit_rate_convert(field_collapse_thousands(audio_bit_rate_str)))
        
    def __repr__(self):
        retStr = "\nInput file: "+ self.input_file_name + "\n\n"
        retStr += "Video:\n"
        retStr += "\tStream ID: " + str(self.vid_stream_id) + "\n"
        retStr += "\tFormat: " + self.vid_format + "\n"
        retStr += "\tCodec ID: "+ self.vid_codec_id + "\n"
        retStr += "\tScan type: " + self.vid_scan + "\n"
        retStr += "\tWidth: " + str(self.vid_width) + "\n"
        retStr += "\tHeight: " + str(self.vid_height) + "\n"
        retStr += "\tBit rate: " + str(self.vid_bitrate) + "\n"
        retStr += "Audio:\n"
        retStr += "\tStream ID: " + str(self.audio_stream_id) + "\n"
        retStr += "\tFormat: " + self.audio_format + "\n"
        retStr += "\tCodec ID: " + self.audio_codec_id + "\n"
        retStr += "\tBit rate: " + str(self.audio_bitrate) + "\n"
        return retStr

if __name__ == "__main__":
    import sys
    testParser = VidParser(sys.argv[1])
    print testParser