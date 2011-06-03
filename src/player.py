#!/usr/bin/python

import sys,subprocess,optparse,vidparse

optparser = optparse.OptionParser()
optparser.add_option("-d","--debug",type="int", dest="debug_level",help="Enable debug logging")
optparser.add_option("-m","--mplayer-opts",action="store", type="string", dest="mplayer_opts",help="Pass additional mplayer options")
(options, extra_args) = optparser.parse_args()

if (not options.mplayer_opts):
    options.mplayer_opts = ""

if len(extra_args) == 0:
    print "No filename specified, exiting."
    sys.exit()

DECISION_LOG = options.debug_level

vidInfo = vidparse.VidParser(extra_args[0])

# Decision steps
vdpau_codec=""
#vdpau_opts=":sharpen=0.4:denoise=0.4"
vdpau_opts=""
sw_opts=""

# Deinterlace for non-progressive videos
if (vidInfo.vid_interlaced == True):
    vdpau_opts = vdpau_opts + ":deint=4"
    sw_opts = sw_opts + "-vf pp=yadif:1"

# HQ scaling only if video isn't in native resolution
if (vidInfo.vid_width != 1920) and (vidInfo.vid_height != 1080):
    vdpau_opts = vdpau_opts + ":hqscaling=1"

# Codec selection
if (vidInfo.vid_codec == vidparse.VIDEO_CODEC_H264):
        vdpau_codec = "-vc ffh264vdpau"
elif (vidInfo.vid_codec == vidparse.VIDEO_CODEC_WMV3):
        vdpau_codec = "-vc ffwmv3vdpau"
elif (vidInfo.vid_codec == vidparse.VIDEO_CODEC_DIVX):
        vdpau_codec = "-vc ffodivxvdpau"
elif (vidInfo.vid_codec == vidparse.VIDEO_CODEC_MPEG12):
        vdpau_codec = "-vc ffmpeg12vdpau"
elif (vidInfo.vid_codec == vidparse.VIDEO_CODEC_VC1):
        vdpau_codec = "-vc ffvc1vdpau"

if DECISION_LOG >= 1:
    print "VDPAU options: " + vdpau_opts
    print "VDPAU codec: " + vdpau_codec
    print "S/W options: " + sw_opts

mplayer_cmdline = "-vo vdpau" + vdpau_opts + " " + vdpau_codec + " " + options.mplayer_opts + " \"" + "".join(extra_args[0:]) +"\""
print "Running: mplayer2 " + mplayer_cmdline + "\n"

p = subprocess.Popen("mplayer2 " + mplayer_cmdline, shell=True, stderr=subprocess.PIPE)
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
    mplayer_cmdline = sw_opts + " " + options.mplayer_opts + " \"" + "".join(extra_args[0:]) + "\""
    print "Running: mplayer2 " + mplayer_cmdline + "\n"

    p = subprocess.Popen("mplayer2 " + mplayer_cmdline, shell=True)
    p.communicate()

sys.exit()
