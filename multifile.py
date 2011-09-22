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

import vidparse

READ_BUFFER_SIZE = 4 * 1024 # 4KB per buffer read iteration

class MultiFileInput:
    """Multiple input file implementation"""
    
    _current_idx = -1
    _current_file = None
    _output_fd = None

    parser = None
    
    def _compare_parsers(self, parser1, parser2):
        if parser1.vid_fps != parser2.vid_fps:
            raise Exception("Differing FPS: " + str(parser1.vid_fps) +
                            " != " + str(parser2.vid_fps))
        if parser1.vid_width != parser2.vid_width:
            raise Exception("Differing width: " + str(parser1.vid_width) +
                            " != " + str(parser2.vid_width))
        if parser1.vid_height != parser2.vid_height:
            raise Exception("Differing height: " + str(parser1.vid_height) +
                            " != " + str(parser2.vid_height))
        if parser1.vid_interlaced != parser2.vid_interlaced:
            raise Exception("Differing interlace setting: " +
                            str(parser1.vid_interlaced) +
                            " != " + str(parser2.vid_interlaced))
        if parser1.vid_codec != parser2.vid_codec:
            raise Exception("Differing video codec: " + parser1.vid_codec +
                            " != " + parser2.vid_codec)
        if parser1.audio_codec_id != parser2.audio_codec_id:
            raise Exception("Differing audio codec: " +
                            parser1.audio_codec_id +
                            " != " + parser2.audio_codec_id)
        if parser1.audio_channels != parser2.audio_channels:
            raise Exception("Differing audio channel count: " +
                            str(parser1.audio_channels) +
                            " != " + str(parser2.audio_channels))
        if parser1.audio_samplerate != parser2.audio_samplerate:
            raise Exception("Differing audio sample rate: " +
                            str(parser1.audio_samplerate) +
                            " != " + str(parser2.audio_samplerate))
        
    def _validate_list(self, file_list):
        '''Validate the input cur_file list to make sure all files are similar'''
        print "Validating multiple cur_file compatibility..."
        
        for cur_file in file_list:
            if self.parser == None:
                try:
                    self.parser = vidparse.VidParser(cur_file)
                except Exception as e:
                    raise e
            else:
                try:
                    cur_parser = vidparse.VidParser(cur_file)
                except Exception as e:
                    raise e

                try:
                    self._compare_parsers(self.parser, cur_parser)
                except Exception as e:
                    print ("Files '" + file_list[0] + "' and '" + cur_file +
                           "' are incompatible:")
                    raise e
        
        print "All files compatible!"
    
    def _open_next(self):
        '''Opens the next file in the list and sets current file appropriately'''
        if self._current_file != None:
            self._current_file.close()
        self._current_idx += 1
        if self._current_idx < len(self._file_list):
            self._current_file = open(self._file_list[self._current_idx], 'rb')
        else:
            self._current_file = None

    def _read(self):
        '''Reads data from the current file and returns it'''
        buf = ""
        
        if (self._current_idx == -1):
            self._open_next()

        if self._current_file != None:    
            buf = self._current_file.read(READ_BUFFER_SIZE)

        if buf == "":
            self._open_next()
            if self._current_file != None:
                buf = self._current_file.read(READ_BUFFER_SIZE)

        return buf

    def __init__(self, file_list):
        try:
            self._validate_list(file_list)
        except Exception as e:
            raise e
        self._file_list = file_list

    def set_output(self, output_fd):
        '''Set the output file descriptor for write_all() to write to'''
        self._output_fd = output_fd

    def write_all(self):
        '''Read all the files in the input list and write them to the output set with set_output()'''
        buf = self._read()
        while buf != "":
            try:
                self._output_fd.write(buf)
            except:
                # Output file descriptor closed, reader process is gone...
                return
            buf = self._read()
        self._output_fd.close()
    
    def rewind(self):
        '''Rewind to the beginning of the input list'''
        if self._current_file != None:
            self._current_file.close()
            self._current_file = None
        self._current_idx = -1