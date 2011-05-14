#!/usr/bin/python

import subprocess, re

def get_field_value(line_str):
    splitter = re.compile(r'[:]+')
    line_tokenized = splitter.split(line_str)
    return line_tokenized[len(line_tokenized) - 1][1:]

def tokenize_field(field_str):
    splitter = re.compile(r'[ ]+')
    return splitter.split(field_str)

def field_collapse_thousands(field_str):
    result = []
    field_str_tokenized = tokenize_field(field_str)
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
    
    input_file_name = ""
    
    # Video parameters
    vid_stream_id = -1
    vid_format = ""
    vid_codec_id = ""
    vid_scan = ""
    vid_width = 0
    vid_height = 0
    vid_bitrate = 0
    vid_fps = 0.0
    
    # Audio parameters
    audio_stream_id = -1
    audio_format = ""
    audio_codec_id = ""
    audio_channels = 0
    audio_bitrate = 0
    audio_samplerate = 0

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
                if mp_line.startswith("Format  "):
                    self.vid_format = get_field_value(mp_line)
                elif mp_line.startswith("Codec ID "):
                    self.vid_codec_id = get_field_value(mp_line)
                elif  mp_line.startswith("ID "):
                    self.vid_stream_id = int(tokenize_field(get_field_value(mp_line))[0])
                elif mp_line.startswith("Scan type "):
                    self.vid_scan = get_field_value(mp_line)
                elif mp_line.startswith("Width "):
                    vid_width_str = get_field_value(mp_line)
                    self.vid_width = int(field_collapse_thousands(vid_width_str)[0])
                elif mp_line.startswith("Height "):
                    vid_height_str = get_field_value(mp_line)
                    self.vid_height = int(field_collapse_thousands(vid_height_str)[0])
                elif mp_line.startswith("Bit rate  "):
                    vid_bit_rate_str = get_field_value(mp_line)
                    self.vid_bitrate = int(bit_rate_convert(field_collapse_thousands(vid_bit_rate_str)))
                elif mp_line.startswith("Frame rate  "):
                    vid_fps_str = get_field_value(mp_line)
                    self.vid_fps = float(tokenize_field(vid_fps_str)[0])
            elif current_section == AUDIO_SECTION:
                if mp_line.startswith("Format  "):
                    self.audio_format = get_field_value(mp_line)
                elif mp_line.startswith("Codec ID "):
                    self.audio_codec_id = get_field_value(mp_line)
                elif mp_line.startswith("ID"):
                    self.audio_stream_id = int(tokenize_field(get_field_value(mp_line))[0])
                elif mp_line.startswith("Bit rate  "):
                    audio_bit_rate_str = get_field_value(mp_line)
                    self.audio_bitrate = int(bit_rate_convert(field_collapse_thousands(audio_bit_rate_str)))
                elif mp_line.startswith("Sampling rate "):
                    audio_sample_rate_str = get_field_value(mp_line)
                    self.audio_samplerate = int(float_to_str_trunc(float(tokenize_field(audio_sample_rate_str)[0])))
                elif mp_line.startswith("Channel(s) "):
                    audio_channel_str = get_field_value(mp_line)
                    self.audio_channels = int(tokenize_field(audio_channel_str)[0])
        
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
        retStr += "\tFPS: " + str(self.vid_fps) + "\n"
        retStr += "Audio:\n"
        retStr += "\tStream ID: " + str(self.audio_stream_id) + "\n"
        retStr += "\tFormat: " + self.audio_format + "\n"
        retStr += "\tCodec ID: " + self.audio_codec_id + "\n"
        retStr += "\tChannel count: " + str(self.audio_channels) + "\n"
        retStr += "\tBit rate: " + str(self.audio_bitrate) + "\n"
        retStr += "\tSample rate: " + str(self.audio_samplerate) + "\n"
        return retStr

if __name__ == "__main__":
    import sys
    testParser = VidParser(sys.argv[1])
    print testParser