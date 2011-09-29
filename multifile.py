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

from mmf import vidparse
from mmf import errors

_READ_BUFFER_SIZE = 4 * 1024 # 4KB per buffer read iteration

class MultiFileInput:
    """Multiple input file implementation"""
    
    def __init__(self, file_list):
        self.parser = None
        self._current_file = None
        self._current_idx = -1
        
        try:
            self._validate_list(file_list)
        except errors.MMFError:
            raise
        self._file_list = file_list
        self._output_fd = None 
        
    def _validate_list(self, file_list):
        """Validate the input file list to make sure all files are similar"""
        print "Validating multiple file compatibility..."

        for cur_file in file_list:
            if self.parser is None:
                try:
                    self.parser = vidparse.VidParser(cur_file)
                except errors.MMFError:
                    raise
            else:
                try:
                    cur_parser = vidparse.VidParser(cur_file)
                except errors.MMFError:
                    raise

                if cur_parser != self.parser:
                    raise errors.MMFError(
                        "Files '%s' and '%s' are incompatible:\n%s" %
                        (file_list[0], cur_file, cur_parser.diff_str))

        # TODO: Validate that the file containers are concat-able
        
        print "All files compatible!"
    
    def _open_next(self):
        """Opens the next file in the list and sets current file appropriately"""
        if self._current_file is not None:
            self._current_file.close()
        self._current_idx += 1
        if self._current_idx < len(self._file_list):
            self._current_file = open(self._file_list[self._current_idx], 'rb')
        else:
            self._current_file = None

    def _read(self):
        """Reads data from the current file and returns it"""
        buf = ""
        
        if (self._current_idx == -1):
            self._open_next()

        if self._current_file is not None:
            buf = self._current_file.read(_READ_BUFFER_SIZE)

        if buf == "":
            self._open_next()
            if self._current_file is not None:
                buf = self._current_file.read(_READ_BUFFER_SIZE)

        return buf

    def set_output(self, output_fd):
        """Set the output file descriptor for write_all() to write to"""
        self._output_fd = output_fd

    def write_all(self):
        """
        Read all the files in the input list and write them to the output
        set with set_output()
        """
        if self._output_fd is None:
            raise errors.MMFError(
                "No output descriptor set for %s" % self)

        buf = self._read()
        while buf != "":
            try:
                self._output_fd.write(buf)
            except IOError:
                # Output file descriptor closed, reader process is gone...
                raise
            buf = self._read()
        self._output_fd.close()
    
    def rewind(self):
        """Rewind to the beginning of the input list"""
        if self._current_file is not None:
            self._current_file.close()
            self._current_file = None
        self._current_idx = -1