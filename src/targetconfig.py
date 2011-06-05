#!/usr/bin/python
# Mark's Media Framework 
# Copyright (C) 2011  Mark Pariente
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import os.path, re

TARGET_FILE_EXTENSION=".mmftarget"
TARGET_DIRECTORY="targets"

def find_target_file(target_string):
    if TARGET_FILE_EXTENSION in target_string:
        target_file = target_string
    else:
        target_file = target_string + TARGET_FILE_EXTENSION
    
    if os.path.isfile(target_file):
        return target_file
    elif os.path.isfile(TARGET_DIRECTORY + "/" + target_file):
        return TARGET_DIRECTORY + "/" + target_file
    else:
        return ""

def get_string_field(line_str):
    splitter = re.compile(r'=[ ]*')
    line_tokenized = splitter.split(line_str)
    string_token = line_tokenized[len(line_tokenized) - 1][1:]
    string_token = string_token.replace('\n','')
    string_token = string_token.replace('\"','')
    return string_token

def get_int_field(line_str):
    splitter = re.compile(r'=[ ]*')
    line_tokenized = splitter.split(line_str)
    result = line_tokenized[len(line_tokenized) - 1]
    result = result.replace('\n','')
    return int(result)

class TargetConfig:
    """Target device configuration"""
    
    target_file = "NOT FOUND"
    target_name = ""
    
    video_max_width = 0
    video_max_height = 0
    video_max_bitrate = 0
    
    codec_h264_profile = ""
    codec_h264_level = ""
    
    audio_max_bitrate = 0
    audio_sample_rate = 0
    audio_channel_count = 0

    def __init__(self, target_string):
        target_file = find_target_file(target_string)
        if target_file != "":
            self.target_file = target_file
        else:
            raise Exception("Target file for '" + target_string + "' not found.")
        
        file = open(self.target_file, 'r')
        for line in file:
            if line.startswith("TARGET_NAME_STRING"):
                self.target_name = get_string_field(line)
            elif line.startswith("VIDEO_MAX_WIDTH"):
                self.video_max_width = get_int_field(line)
            elif line.startswith("VIDEO_MAX_HEIGHT"):
                self.video_max_height = get_int_field(line)
            elif line.startswith("VIDEO_MAX_BITRATE"):
                self.video_max_bitrate = get_int_field(line)
            elif line.startswith("CODEC_H264_PROFILE"):
                self.codec_h264_profile = get_string_field(line)
            elif line.startswith("CODEC_H264_LEVEL"):
                self.codec_h264_level = get_string_field(line)
            elif line.startswith("AUDIO_MAX_BITRATE"):
                self.audio_max_bitrate = get_int_field(line)
            elif line.startswith("AUDIO_SAMPLE_RATE"):
                self.audio_sample_rate = get_int_field(line)
            elif line.startswith("AUDIO_CHANNEL_COUNT"):
                self.audio_channel_count = get_int_field(line)

    def __repr__(self):
        retStr = "\nTarget file: "+ self.target_file + "\n"
        retStr += "Target name: " + self.target_name + "\n"
        retStr += "Video:\n"
        retStr += "\tMax width: " + str(self.video_max_width) + "\n"
        retStr += "\tMax height: " + str(self.video_max_height) + "\n"
        retStr += "\tMax bitrate: " + str(self.video_max_bitrate) + "\n"
        retStr += "\tH264 profile: " + self.codec_h264_profile + "\n"
        retStr += "\tH264 level: " + self.codec_h264_level + "\n"
        retStr += "Audio:\n"
        retStr += "\tMax bitrate: " + str(self.audio_max_bitrate) + "\n"
        retStr += "\tSample rate: " + str(self.audio_sample_rate) + "\n"
        retStr += "\tChannel count: " + str(self.audio_channel_count) + "\n"
        return retStr

if __name__ == "__main__":
    import sys
    testConfig = TargetConfig(sys.argv[1])
    print testConfig
        