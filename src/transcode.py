#!/usr/bin/python

import sys,subprocess,optparse,vidparse,targetconfig

optparser = optparse.OptionParser()
optparser.add_option("-o","--output",action="store", type="string", dest="output_file",help="Output file name")
optparser.add_option("-t","--target",action="store", type="string", dest="target_string",help="Target device name")
(options, extra_args) = optparser.parse_args()

if (options.output_file == None):
    print "No output file specified, exiting."
    sys.exit()

if (options.target_string == None):
    print "No target specified, exiting."
    sys.exit()

if len(extra_args) == 0:
    print "No input file specified, exiting."
    sys.exit()
else:
    input_file = extra_args[0]

try:
    vid_info = vidparse.VidParser(input_file)
except:
    print sys.exc_info()[1]
    sys.exit()

try:
    target_config = targetconfig.TargetConfig(options.target_string)
except:
    print sys.exc_info()[1]
    sys.exit() 

# Audio encode
ffmpeg_cmdline = "ffmpeg -v 0 -y -i " + input_file + " -vn -acodec pcm_s16le -ac " + str(target_config.audio_channel_count) + " -ar " + str(target_config.audio_sample_rate) + " -f wav pipe:1 2> /dev/null"
print ffmpeg_cmdline
ffmpeg = subprocess.Popen(ffmpeg_cmdline, shell = True, stdout = subprocess.PIPE)

#TODO: use a temp file instead of output-audio.aac
audio_bitrate = min(vid_info.audio_bitrate, target_config.audio_max_bitrate) * 1000
neroaac_cmdline = "/opt/neroaac/1.5.1/neroAacEnc -cbr " + str(audio_bitrate) + " -lc -ignorelength -if - -of output-audio.aac"
print neroaac_cmdline
neroaac = subprocess.Popen(neroaac_cmdline, shell = True, stdin = ffmpeg.stdout)

while ffmpeg.returncode is not None:
    buffer = ffmpeg.communicate()
    neroaac.communicate(buffer)

neroaac.wait()

# Video parameter calculations
h264_level_str = target_config.codec_h264_level.replace('.', '')
h264_profile_str = target_config.codec_h264_profile.lower()

if (vid_info.vid_width > target_config.video_max_width) or (vid_info.vid_height > target_config.video_max_height):
    vid_size_str = "-s " + str(target_config.video_max_width) + "x" + str(target_config.video_max_height) #TODO: Fix aspect ratio
    bit_rate = target_config.video_max_bitrate
else:
    vid_size_str = ""
    # Adjust bitrate fractionally based on max bitrate
    bit_rate = int(target_config.video_max_bitrate * (float(vid_info.vid_width * vid_info.vid_height) / float(target_config.video_max_width * target_config.video_max_height)))

vid_bitrate_str = str(bit_rate * 1000)

# Stream mapping calculation
if (vid_info.audio_stream_id > vid_info.vid_stream_id):
    map_vid_str = "-map 0:0"
    map_audio_str = "-map 1:0"
else:
    map_vid_str = "-map 0.1:0.1"
    map_audio_str = "-map 1.0:1"

# Video first pass
#TODO: Do this stuff in a tempdir so x264 logfiles don't clash between multiple invocations
ffmpeg_cmdline = "ffmpeg -y -an -i " + input_file + " " + vid_size_str + " -pass 1 -vcodec libx264 -threads 0 -level " + h264_level_str + " -preset slow -profile " + h264_profile_str + " -b " + vid_bitrate_str + " -f rawvideo /dev/null"
print ffmpeg_cmdline
ffmpeg = subprocess.Popen(ffmpeg_cmdline, shell = True)
ffmpeg.wait()

# Video second pass + muxer step
ffmpeg_cmdline = "ffmpeg -y " + map_vid_str + " -i " + input_file + " " + map_audio_str + " -i output-audio.aac " + vid_size_str + " -pass 2 -vcodec libx264 -threads 0 -level " + h264_level_str + " -preset slow -profile " + h264_profile_str + " -b " + vid_bitrate_str + " -acodec copy " + options.output_file
print ffmpeg_cmdline
ffmpeg = subprocess.Popen(ffmpeg_cmdline, shell = True)
ffmpeg.wait()

# Clean up intermediate files
cleanup = subprocess.Popen("rm x264_2pass.log* output-audio.aac", shell = True)
cleanup.wait()