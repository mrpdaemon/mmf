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

import optparse
import subprocess
import sys

from mmf import vidparse
from mmf import errors

def main(argv = sys.argv):
    optparser = optparse.OptionParser()
    optparser.add_option("-d", "--debug", type="int", dest="debug_level",
                         help="Enable debug logging")
    optparser.add_option("-m", "--mplayer-opts", action="store",
                         type="string", dest="mplayer_opts",
                         help="Pass additional mplayer options")
    optparser.add_option("-2", "--use-mplayer2", action = "store_true",
                         dest="use_mplayer2",
                         help="Use mplayer2 instead of mplayer")
    (options, extra_args) = optparser.parse_args()
    
    if not options.mplayer_opts:
        options.mplayer_opts = ""
    
    if not options.use_mplayer2:
        options.use_mplayer2 = False
    
    if len(extra_args) == 0:
        print "No filename specified, exiting."
        sys.exit(1)
    
    DECISION_LOG = options.debug_level
    
    try:
        vid_info = vidparse.VidParser(extra_args[0])
    except errors.MMFError as e:
        print e.msg
        sys.exit(1)
    
    # Decision steps
    vdpau_codec=""
    vdpau_opts=""
    sw_opts=""
    
    # Deinterlace for non-progressive videos
    if vid_info.vid_interlaced is not None:
        if vid_info.vid_interlaced:
            vdpau_opts = vdpau_opts + ":deint=4"
            sw_opts = sw_opts + "-vf pp=yadif:1"
        else:
            # Sharpen and de-noise progressive videos. Using these filters in
            # conjunction with deinterlace puts too much load on the GPU
            vdpau_opts = vdpau_opts + ":sharpen=0.4:denoise=0.4"

    # HQ scaling only if video isn't in native resolution
    if (vid_info.vid_width is not None) and (vid_info.vid_height is not None):
        if vid_info.vid_width != 1920 and vid_info.vid_height != 1080:
            vdpau_opts = vdpau_opts + ":hqscaling=1"          
    
    # Codec selection
    if vid_info.vid_codec is not None:  
        if vid_info.vid_codec == vidparse.VIDEO_CODEC_H264:
            vdpau_codec = "-vc ffh264vdpau"
        elif vid_info.vid_codec == vidparse.VIDEO_CODEC_WMV3:
            vdpau_codec = "-vc ffwmv3vdpau"
        elif vid_info.vid_codec == vidparse.VIDEO_CODEC_DIVX:
            vdpau_codec = "-vc ffodivxvdpau"
        elif vid_info.vid_codec == vidparse.VIDEO_CODEC_MPEG12:
            vdpau_codec = "-vc ffmpeg12vdpau"
        elif vid_info.vid_codec == vidparse.VIDEO_CODEC_VC1:
            vdpau_codec = "-vc ffvc1vdpau"
        
    if DECISION_LOG >= 1:
        print "VDPAU options: " + vdpau_opts
        print "VDPAU codec: " + vdpau_codec
        print "S/W options: " + sw_opts
    
    if options.use_mplayer2:
        mplayer_str = "mplayer2"
    else:
        mplayer_str = "mplayer"
    
    mplayer_cmdline = ("-vo vdpau" + vdpau_opts + " " + vdpau_codec + " " +
                       options.mplayer_opts + " \"" + "".join(extra_args[0:]) +
                       "\"")
    print "Running: " + mplayer_str + " " + mplayer_cmdline + "\n"
    
    p = subprocess.Popen(mplayer_str + " " + mplayer_cmdline, shell=True,
                         stderr=subprocess.PIPE)
    p_errlog = p.communicate()
    p_errlog_tokenized = p_errlog[1].split("\n")
    
    fatal = 0
    for p_errlog_line in p_errlog_tokenized:
        if "FATAL:" in p_errlog_line:
            fatal = 1
    
    if fatal == 1:
        print ""
        print "== Hardware decoding FAILED. Falling back to software. =="
        print ""
        mplayer_cmdline = (sw_opts + " " + options.mplayer_opts + " \"" +
                           "".join(extra_args[0:]) + "\"")
        print "Running: " + mplayer_str + " " + mplayer_cmdline + "\n"
    
        p = subprocess.Popen(mplayer_str + " " + mplayer_cmdline, shell=True)
        p.communicate()