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
import subprocess

from mmf import errors

VIDEO_CODEC_H264 = "H.264"
VIDEO_CODEC_WMV3 = "WMV3"
VIDEO_CODEC_DIVX = "DIVX"
VIDEO_CODEC_MPEG12 = "MPEG 1/2"
VIDEO_CODEC_VC1 = "VC-1"
VIDEO_CODEC_XVID = "XVID"

def _get_field_value(line_str):
    splitter = re.compile(r'[:]+')
    line_tokenized = splitter.split(line_str)
    return line_tokenized[len(line_tokenized) - 1][1:]

def _tokenize_field(field_str):
    splitter = re.compile(r'[ ]+')
    return splitter.split(field_str)

def _field_collapse_thousands(field_str):
    result = []
    field_str_tokenized = _tokenize_field(field_str)
    if len(field_str_tokenized) == 3: # need to combine first 2
        result.append(field_str_tokenized[0] + field_str_tokenized[1])
        result.append(field_str_tokenized[2])
    else:
        result.append(field_str_tokenized[0])
        result.append(field_str_tokenized[1])
    return result

def _float_to_str_trunc(float_val):
    return str(round(float_val, 0))[:-2]

def _bit_rate_convert(bit_rate_tokenized):
    if bit_rate_tokenized[1] == "Kbps":
        return _float_to_str_trunc(float(bit_rate_tokenized[0]))
    elif bit_rate_tokenized[1] == "Mbps":
        return _float_to_str_trunc(float(bit_rate_tokenized[0]) * 1024)
    else:
        raise errors.MMFError("Unknown bit rate string")
                 
class VidParser:
    """Video file parser class using mediainfo"""

    INVALID_SECTION = 0
    VIDEO_SECTION = 1
    AUDIO_SECTION = 2
    TEXT_SECTION = 3
        
    def __init__(self, input_file_name):
        self.vid_stream_id = None
        self.vid_format_profile = None
        self.vid_codec = None
        self.vid_interlaced = None
        self.vid_width = None
        self.vid_height = None
        self.vid_bitrate = None
        self.vid_fps = None
        self._vid_codec_id = None
        self._vid_format = None

        self.audio_stream_id = None
        self.audio_format = None
        self.audio_codec_id = None
        self.audio_channels = None
        self.audio_bitrate = None
        self.audio_samplerate = None

        self.diff_str = None        
    
        if not os.path.isfile(input_file_name):
            raise errors.MMFError("Input file '%s' not found." %
                                  input_file_name);

        self.input_file_name = input_file_name
        current_section = VidParser.INVALID_SECTION
        
        mp = subprocess.Popen(['mediainfo', "".join(input_file_name)],
                              stdout=subprocess.PIPE)
        mp_output = mp.communicate()
        
        mp_tokenized = mp_output[0].split("\n")
        for mp_line in mp_tokenized:
            if mp_line == "Video":
                current_section = VidParser.VIDEO_SECTION
            elif mp_line == "Audio" or mp_line == "Audio #1":
                current_section = VidParser.AUDIO_SECTION
            elif mp_line == "Text":
                current_section = VidParser.TEXT_SECTION
            elif current_section == VidParser.VIDEO_SECTION:
                if mp_line.startswith("Format  "):
                    self._vid_format = _get_field_value(mp_line)
                elif mp_line.startswith("Format profile "):
                    self.vid_format_profile = _get_field_value(mp_line)
                elif mp_line.startswith("Codec ID "):
                    self._vid_codec_id = _get_field_value(mp_line)
                elif  mp_line.startswith("ID "):
                    self.vid_stream_id = int(_tokenize_field(
                        _get_field_value(mp_line))[0])
                elif mp_line.startswith("Scan type "):
                    vid_scan = _get_field_value(mp_line)
                    if (vid_scan == "Interlaced") or (vid_scan == "MBAFF"):
                        self.vid_interlaced = True
                    elif (vid_scan == "Progressive"):
                        self.vid_interlaced = False
                elif mp_line.startswith("Width "):
                    vid_width_str = _get_field_value(mp_line)
                    self.vid_width = int(_field_collapse_thousands(
                        vid_width_str)[0])
                elif mp_line.startswith("Height "):
                    vid_height_str = _get_field_value(mp_line)
                    self.vid_height = int(_field_collapse_thousands(
                        vid_height_str)[0])
                elif mp_line.startswith("Bit rate  "):
                    vid_bit_rate_str = _get_field_value(mp_line)
                    self.vid_bitrate = int(_bit_rate_convert(
                        _field_collapse_thousands(vid_bit_rate_str)))
                elif mp_line.startswith("Frame rate  "):
                    vid_fps_str = _get_field_value(mp_line)
                    self.vid_fps = float(_tokenize_field(vid_fps_str)[0])
            elif current_section == VidParser.AUDIO_SECTION:
                if mp_line.startswith("Format  "):
                    self.audio_format = _get_field_value(mp_line)
                elif mp_line.startswith("Codec ID "):
                    self.audio_codec_id = _get_field_value(mp_line)
                elif mp_line.startswith("ID"):
                    self.audio_stream_id = int(_tokenize_field(
                        _get_field_value(mp_line))[0])
                elif mp_line.startswith("Bit rate  "):
                    audio_bit_rate_str = _get_field_value(mp_line)
                    self.audio_bitrate = int(_bit_rate_convert(
                        _field_collapse_thousands(audio_bit_rate_str)))
                elif mp_line.startswith("Sampling rate "):
                    audio_sample_rate_str = _get_field_value(mp_line)
                    self.audio_samplerate = int(_float_to_str_trunc(
                        float(_tokenize_field(audio_sample_rate_str)[0])))
                elif mp_line.startswith("Channel(s) "):
                    audio_channel_str = _get_field_value(mp_line)
                    self.audio_channels = int(_tokenize_field(
                        audio_channel_str)[0])

        if (self._vid_codec_id == "avc1" or
            self._vid_codec_id == "V_MPEG4/ISO/AVC" or
            self._vid_format == "AVC"):
            self.vid_codec = VIDEO_CODEC_H264
        elif self._vid_codec_id == "WMV3":
            self.vid_codec = VIDEO_CODEC_WMV3
        elif self._vid_codec_id == "DX40" or self._vid_codec_id == "DIVX":
            self.vid_codec = VIDEO_CODEC_DIVX
        elif self._vid_format == "MPEG Video":
            self.vid_codec = VIDEO_CODEC_MPEG12
        elif self._vid_format == "VC-1":
            self.vid_codec = VIDEO_CODEC_VC1
        elif self._vid_codec_id == "XVID":
            self.vid_codec = VIDEO_CODEC_XVID
                
        try:
            self._validate()
        except errors.MMFError:
            raise

    def _validate(self):
        if self.vid_fps is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no FPS found" %
                self.input_file_name)
        if self.vid_width is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no video width found" %
                self.input_file_name)
        if self.vid_height is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no video height found" %
                self.input_file_name)
        if self.vid_interlaced is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no scan info found" %
                self.input_file_name)
        if self.vid_codec is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no video codec found" %
                self.input_file_name)
        if self.audio_codec_id is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no audio codec found" %
                self.input_file_name)
        if self.audio_channels is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no audio channels found" %
                self.input_file_name)
        if self.audio_samplerate is None:
            raise errors.MMFError(
                "Failed to parse video file '%s' - no audio sample rate found" %
                self.input_file_name)
         
    def __eq__(self, other):
        """Equality operator for two parser objects"""
        if self.vid_fps != other.vid_fps:
            self.diff_str = ("Differing FPS: %s != %s" %
                             (str(self.vid_fps), str(other.vid_fps)))
            return False
        if self.vid_width != other.vid_width:
            self.diff_str = ("Differing width: %s != %s" %
                             (str(self.vid_width), str(other.vid_width)))
            return False
        if self.vid_height != other.vid_height:
            self.diff_str = ("Differing height: %s != %s" %
                             (str(self.vid_height), str(other.vid_height)))
            return False
        if self.vid_interlaced != other.vid_interlaced:
            self.diff_str = ("Differing interlace setting: %s != %s" %
                             (str(self.vid_interlaced),
                              str(other.vid_interlaced)))
            return False
        if self.vid_codec != other.vid_codec:
            self.diff_str = ("Differing video codec: %s != %s" %
                             (str(self.vid_codec), str(other.vid_codec)))
            return False
        if self.audio_codec_id != other.audio_codec_id:
            self.diff_str = ("Differing audio codec: %s != %s" %
                             (str(self.audio_codec_id),
                              str(other.audio_codec_id)))
            return False
        if self.audio_channels != other.audio_channels:
            self.diff_str = ("Differing audio channel count: %s != %s" %
                             (str(self.audio_channels),
                              str(other.audio_channels)))
            return False
        if self.audio_samplerate != other.audio_samplerate:
            self.diff_str = ("Differing audio sample rate: %s != %s" %
                             (str(self.audio_sample_rate),
                              str(other.audio_sample_rate)))
            return False
        return True
    
    def __ne__(self, other):
        """NOT equal operator for two parser objects"""
        return not self.__eq__(other)

    def __repr__(self):
        retStr = "\nInput file: %s\n" % self.input_file_name
        retStr += "\nVideo:\n"
        retStr += "\tStream ID: %s\n" % str(self.vid_stream_id)
        retStr += "\tFormat profile: %s\n" % self.vid_format_profile
        retStr += "\tCodec: %s\n" % self.vid_codec
        retStr += "\tInterlaced: %s\n" % str(self.vid_interlaced)
        retStr += "\tWidth: %s\n" % str(self.vid_width)
        retStr += "\tHeight: %s\n" % str(self.vid_height)
        retStr += "\tBit rate: %s\n" % str(self.vid_bitrate)
        retStr += "\tFPS: %s\n" % str(self.vid_fps)
        retStr += "Audio:\n"
        retStr += "\tStream ID: %s\n" % str(self.audio_stream_id)
        retStr += "\tFormat: %s\n" % self.audio_format
        retStr += "\tCodec ID: %s\n" % self.audio_codec_id
        retStr += "\tChannel count: %s\n" % str(self.audio_channels)
        retStr += "\tBit rate: %s\n" % str(self.audio_bitrate)
        retStr += "\tSample rate: %s\n" % str(self.audio_samplerate)
        return retStr

if __name__ == "__main__":
    import sys
    testParser = VidParser(sys.argv[1])
    print testParser