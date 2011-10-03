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

import os.path
import re

from mmf import errors

TARGET_FILE_EXTENSION=".mmftarget"
TARGET_DIRECTORY="targets"
INSTALL_ENV_VAR="MMF_INSTALL_DIR"

def find_target_file(target_string):
    """Finds the target file location given a target string"""
    
    # Grab the install directory from the environment variable
    env_dir = os.getenv(INSTALL_ENV_VAR);
    if env_dir is not None:
        target_prefix = "%s/%s" % (env_dir, TARGET_DIRECTORY)
    else:
        target_prefix = TARGET_DIRECTORY;

    # Add extension if not specified
    if TARGET_FILE_EXTENSION in target_string:
        target_file = target_string
    else:
        target_file = target_string + TARGET_FILE_EXTENSION
    
    if os.path.isfile(target_file):
        return target_file
    elif os.path.isfile("%s/%s" % (target_prefix, target_file)):
        return "%s/%s" % (target_prefix, target_file)
    else:
        return None

def _get_string_field(line_str):
    splitter = re.compile(r'=[ ]*')
    line_tokenized = splitter.split(line_str)
    string_token = line_tokenized[len(line_tokenized) - 1][1:]
    string_token = string_token.replace('\n','')
    string_token = string_token.replace('\"','')
    return string_token

def _get_int_field(line_str):
    splitter = re.compile(r'=[ ]*')
    line_tokenized = splitter.split(line_str)
    result = line_tokenized[len(line_tokenized) - 1]
    result = result.replace('\n','')
    return int(result)


class TargetConfig:
    """Class that represents a target device configuration"""

    def _validate(self):
        """ Validate that required fields are present""" 
        if self.video_max_width is None:
            raise errors.MMFError(
                "Incomplete target file %s - no video width specified" %
                self.target_file)
        if self.video_max_height is None:
            raise errors.MMFError(
                "Incomplete target file %s - no video height specified" %
                self.target_file)
        if self.video_max_bitrate is None:
            raise errors.MMFError(
                "Incomplete target file %s - no video bitrate specified" %
                self.target_file)
        if self.codec_h264_profile is None:
            raise errors.MMFError(
                "Incomplete target file %s - no video codec specified" %
                self.target_file)
        if self.audio_max_bitrate is None:
            raise errors.MMFError(
                "Incomplete target file %s - no audio bitrate specified" %
                self.target_file)
        if self.audio_sample_rate is None:
            raise errors.MMFError(
                "Incomplete target file %s - no audio sample rate specified" %
                self.target_file)
        if self.audio_channel_count is None:
            raise errors.MMFError(
                "Incomplete target file %s - no audio channel count specified" %
                self.target_file)
            
    def __init__(self, target_string):
        """Loads target configuration from file for given target string"""
        
        # Initialize all values - file could be missing fields
        self.target_name = None
        self.video_max_width = None
        self.video_max_height = None
        self.video_max_bitrate = None
        self.video_interlaced = False
        self.codec_h264_profile = None
        self.codec_h264_same = False
        self.codec_h264_level = None
        self.audio_max_bitrate = None
        self.audio_max_samplerate = None
        self.audio_channel_count = None
        
        target_file = find_target_file(target_string)
        if target_file is not None:
            self.target_file = target_file
        else:
            raise errors.MMFError("Target file for '%s' not found." %
                                  target_string)
        
        cur_file = open(self.target_file, 'r')
        for line in cur_file:
            if line.startswith("TARGET_NAME_STRING"):
                self.target_name = _get_string_field(line)
            elif line.startswith("VIDEO_MAX_WIDTH"):
                self.video_max_width = _get_int_field(line)
            elif line.startswith("VIDEO_MAX_HEIGHT"):
                self.video_max_height = _get_int_field(line)
            elif line.startswith("VIDEO_MAX_BITRATE"):
                self.video_max_bitrate = _get_int_field(line)
            elif line.startswith("VIDEO_SCAN"):
                scan_str = _get_string_field(line)
                if scan_str.lower() == "interlaced":
                    self.video_interlaced = True
            elif line.startswith("CODEC_H264_PROFILE"):
                self.codec_h264_profile = _get_string_field(line)
            elif line.startswith("CODEC_H264_LEVEL"):
                self.codec_h264_level = _get_string_field(line)
            elif line.startswith("AUDIO_MAX_BITRATE"):
                self.audio_max_bitrate = _get_int_field(line)
            elif line.startswith("AUDIO_SAMPLE_RATE"):
                self.audio_sample_rate = _get_int_field(line)
            elif line.startswith("AUDIO_CHANNEL_COUNT"):
                self.audio_channel_count = _get_int_field(line)
        
        try:
            self._validate()
        except errors.MMFError:
            raise
        
        if (self.codec_h264_level.lower() == "same" or
            self.codec_h264_profile.lower() == "same"):
            self.codec_h264_same = True

    def __repr__(self):
        retStr = "\nTarget file: "+ self.target_file + "\n"
        retStr += "Target name: %s\n" % self.target_name
        retStr += "Video:\n"
        retStr += "\tMax width: %s\n" % str(self.video_max_width)
        retStr += "\tMax height: %s\n" % str(self.video_max_height)
        retStr += "\tMax bitrate: %s\n" % str(self.video_max_bitrate)
        retStr += "\tH264 profile: %s\n" % self.codec_h264_profile
        retStr += "\tH264 level: %s\n" % self.codec_h264_level
        retStr += "Audio:\n"
        retStr += "\tMax bitrate: %s\n" % str(self.audio_max_bitrate)
        retStr += "\tSample rate: %s\n" % str(self.audio_sample_rate)
        retStr += "\tChannel count: %s\n" % str(self.audio_channel_count)
        return retStr

if __name__ == "__main__":
    import sys
    testConfig = TargetConfig(sys.argv[1])
    print testConfig
        