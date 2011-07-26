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

import sys,shlex,subprocess,optparse,vidparse,targetconfig,tempfile,os,multifile

optparser = optparse.OptionParser()
optparser.add_option("-o","--output",action="store", type="string",
                     dest="output_file",help="Output file name")
optparser.add_option("-t","--target",action="store", type="string",
                     dest="target_string",help="Target device name")
optparser.add_option("-l","--length",type="int", dest="duration",
                     help="Number of seconds to encode (defaults to whole file)")
optparser.add_option("-s","--offset",type="int", dest="start_offset",
                     help="Offset in seconds from the beginning of the input file to skip")
optparser.add_option("-2","--double-pass", action = "store_true",
                     dest="double_pass",
                     help="Use double-pass encoding for better compression efficiency")
optparser.add_option("-p","--preset",action="store", type="string",
                     dest="ffmpeg_preset",
                     help="FFMpeg preset to use for encoding")
optparser.add_option("-n","--use-neroaac", action = "store_true",
                     dest="use_neroaac",
                     help="Use neroAacEnc instead of ffmpeg for audio encoding")
(options, extra_args) = optparser.parse_args()

if options.output_file == None:
    print "No output file specified, exiting."
    sys.exit()

if options.target_string == None:
    print "No target specified, exiting."
    sys.exit()

if len(extra_args) == 0:
    print "No input file specified, exiting."
    sys.exit()
elif len(extra_args) == 1:
    single_file = True
    input_file = extra_args[0]
    input_file_str = " -i " + input_file
else:
    if options.duration or options.start_offset:
        print "Multiple file mode is not compatible with --length or --offset."
        sys.exit()
    single_file = False
    try:
        input_files = multifile.MultiFileInput(extra_args)
    except:
        print sys.exc_info()[1]
        sys.exit() 
    input_file_str = " -i -"

try:
    if single_file == True:
        vid_info = vidparse.VidParser(extra_args[0])
    else:
        vid_info = input_files.parser
except:
    print sys.exc_info()[1]
    sys.exit()

try:
    target_config = targetconfig.TargetConfig(options.target_string)
except:
    print sys.exc_info()[1]
    sys.exit() 

temp_dir = tempfile.mkdtemp()
print "Working directory: " + temp_dir
os.chdir(temp_dir)

# Prepare duration strings
if not options.duration:
    length_str = ""
else:
    length_str = " -t " + str(options.duration)

if not options.start_offset:
    offset_str = ""
else:
    offset_str = " -ss " + str(options.start_offset)

# Audio parameter calculation
audio_bitrate = min(vid_info.audio_bitrate, target_config.audio_max_bitrate)
if audio_bitrate < target_config.audio_max_bitrate:
    # Round up bitrate to a standard step unless it is > 320 in which case just keep it
    audio_bitrate_steps = [320,256,192,160,128,112,96,64,0]
    prev_rate = audio_bitrate
    for rate in audio_bitrate_steps:
        if audio_bitrate > rate:
            audio_bitrate = prev_rate
            break
        prev_rate = rate
audio_bitrate = audio_bitrate * 1000

if options.use_neroaac:
    # Audio encode with neroAacEnc using ffmpeg to convert input to pcm
    ffmpeg_cmdline = ("ffmpeg -v 0 -y" + offset_str + length_str +
                      input_file_str + " -vn -acodec pcm_s16le -ac " +
                      str(target_config.audio_channel_count) + " -ar " + 
                      str(target_config.audio_sample_rate) +
                      " -f wav pipe:1")
    print ffmpeg_cmdline
    ffmpeg_args = shlex.split(ffmpeg_cmdline)
    null_device = open(os.devnull, 'w')
    if single_file == True:
        ffmpeg = subprocess.Popen(ffmpeg_args, stdout = subprocess.PIPE,
                                  stderr = null_device)
    else:
        ffmpeg = subprocess.Popen(ffmpeg_args, stdin = subprocess.PIPE, 
                                  stdout = subprocess.PIPE, stderr = null_device)
    
    try:
        neroaac_dir = os.environ['NEROAAC_DIR']
    except:
        neroaac_dir = ""
    neroaac_path = os.path.join(neroaac_dir, "neroAacEnc")
    neroaac_cmdline = (neroaac_path + " -cbr " + str(audio_bitrate) +
                       " -lc -ignorelength -if - -of output-audio.aac")
    print neroaac_cmdline
    neroaac_args = shlex.split(neroaac_cmdline)
    neroaac = subprocess.Popen(neroaac_args, stdin = ffmpeg.stdout)

    if single_file == True:
        while ffmpeg.returncode != None:
            buffer = ffmpeg.communicate()
            neroaac.communicate(buffer)
        neroaac.wait()
    else:
        input_files.set_output(ffmpeg.stdin)
        input_files.write_all()
    
        # Flush ffmpeg's stdout and kill it, couldn't find any other way of
        # making neroaac drain ffmpeg's stdout without hanging
        ffmpeg.stdout.flush()
        ffmpeg.kill()
        neroaac.wait()

        input_files.rewind()
    
    null_device.close()
    
# Video parameter calculations
if target_config.codec_h264_same == True:
    # use same profile/level as input
    if vid_info.vid_format_profile == "":
        print vid_info
        print "Same H.264 profile/level as input requested, but no info found in input file."
        sys.exit()
    partition = vid_info.vid_format_profile.partition('@')
    h264_profile_str = partition[0].lower()
    h264_level_str = partition[2].replace('.','').replace('L','')
    
else:
    # use target preset for profile/level
    h264_level_str = target_config.codec_h264_level.replace('.', '')
    h264_profile_str = target_config.codec_h264_profile.lower()

video_max_bitrate = min(target_config.video_max_bitrate, vid_info.vid_bitrate)

def calc_scaled_bitrate(target_config, scaled_width, scaled_height):
    return (int(video_max_bitrate * 
            float(scaled_width * scaled_height) /
            float(target_config.video_max_width * 
                  target_config.video_max_height)))

if vid_info.vid_width > target_config.video_max_width:
    # Scale down width and see if height is within maximum allowed
    scale_factor = float(target_config.video_max_width) / vid_info.vid_width
    scaled_height = int(float(vid_info.vid_height) * scale_factor)
    if scaled_height % 2 == 1: # make sure scaled height divisible by 2
        scaled_height += 1
    if scaled_height < target_config.video_max_height:
        vid_size_str = (" -s " + str(target_config.video_max_width) + "x" +
                        str(scaled_height))
        bit_rate = calc_scaled_bitrate(target_config,
                                       target_config.video_max_width,
                                       scaled_height)
    else:
        # Failed, have to break aspect ratio
        vid_size_str = (" -s " + str(target_config.video_max_width) + "x" +
                        str(target_config.video_max_height))
        bit_rate = video_max_bitrate
elif vid_info.vid_height > target_config.video_max_height:
    # Scale down heigth and see if width is within maximum allowed
    scale_factor = float(target_config.video_max_height) / vid_info.vid_height
    scaled_width = int(float(vid_info.vid_width) * scale_factor)
    if scaled_width % 2 == 1: # make sure scaled width divisible by 2
        scaled_width += 1
    if scaled_width < target_config.video_max_width:
        vid_size_str = (" -s " + str(scaled_width) + "x" +
                        str(target_config.video_max_height))
        bit_rate = calc_scaled_bitrate(target_config,
                                       scaled_width,
                                       target_config.video_max_height)
    else:
        # Failed, have to break aspect ratio
        vid_size_str = (" -s " + str(target_config.video_max_width) + "x" +
                        str(target_config.video_max_height))
        bit_rate = video_max_bitrate
else:
    # Video is smaller than target's max width/height, adjust bitrate
    vid_size_str = ""
    bit_rate = calc_scaled_bitrate(target_config,
                                   vid_info.vid_width,
                                   vid_info.vid_height)
vid_bitrate_str = " -b " + str(bit_rate * 1000)

if options.ffmpeg_preset:
    preset_str = " -preset " + options.ffmpeg_preset
else:
    preset_str = ""

# Interlace handling
if vid_info.vid_interlaced:
    deint_str = " -vf yadif=1"
    if vid_info.vid_fps == 23.976:
        fps_str = " -r 24000/1001"
    elif vid_info.vid_fps == 29.970:
        fps_str = " -r 30000/1001"
    else:
        fps_str = " -r " + str(vid_info.vid_fps)
else:
    deint_str = ""
    fps_str = ""

if options.double_pass:
    # Video first pass
    ffmpeg_cmdline = ("ffmpeg -y" + offset_str + length_str + input_file_str +
                      vid_size_str + " -pass 1 -vcodec libx264" +
                      " -threads 0 -level " + h264_level_str + preset_str +
                      " -profile " + h264_profile_str + vid_bitrate_str +
                      deint_str + fps_str + " -acodec copy -f rawvideo /dev/null")
    print ffmpeg_cmdline
    ffmpeg_args = shlex.split(ffmpeg_cmdline)
    if single_file == True:
        ffmpeg = subprocess.Popen(ffmpeg_args)
    else:
        ffmpeg = subprocess.Popen(ffmpeg_args, stdin = subprocess.PIPE)
        input_files.set_output(ffmpeg.stdin)
        input_files.write_all()

    ffmpeg.wait()
    
    if single_file == False:
        input_files.rewind()
    pass_str = " -pass 2"
else:
    pass_str = ""

# Video second (or first) pass + muxer step (+ audio encode if not using neroAac)
if options.use_neroaac:
    # Stream mapping calculation
    if vid_info.audio_stream_id > vid_info.vid_stream_id:
        map_vid_str = " -map 0:0"
        map_audio_str = " -map 1:0"
    else:
        map_vid_str = " -map 0.1:0.1"
        map_audio_str = " -map 1.0:1"

    audio_input_str = map_audio_str + " -i output-audio.aac"
    audio_codec_str = " -acodec copy"
else:
    map_vid_str = ""
    map_audio_str = ""
    audio_input_str = ""
    audio_codec_str = (" -acodec libvo_aacenc -ac " +
                       str(target_config.audio_channel_count) + " -ar " +
                       str(target_config.audio_sample_rate) + " -ab " +
                       str(audio_bitrate))

ffmpeg_cmdline = ("ffmpeg -y" + offset_str + length_str + map_vid_str +
                  input_file_str + audio_input_str + vid_size_str + pass_str +
                  " -vcodec libx264 -threads 0 -level " + h264_level_str +
                  preset_str +" -profile " + h264_profile_str + vid_bitrate_str
                  + deint_str + fps_str + audio_codec_str + " " +
                  options.output_file)
print ffmpeg_cmdline
ffmpeg_args = shlex.split(ffmpeg_cmdline)

if single_file == True:
    ffmpeg = subprocess.Popen(ffmpeg_args)
else:
    ffmpeg = subprocess.Popen(ffmpeg_args, stdin = subprocess.PIPE)
    input_files.set_output(ffmpeg.stdin)
    input_files.write_all()

ffmpeg.wait()

# Clean up intermediate files
if options.use_neroaac:
    os.remove(os.path.join(temp_dir, "output-audio.aac"))
if options.double_pass:
    os.remove(os.path.join(temp_dir, "x264_2pass.log.mbtree"))
    os.remove(os.path.join(temp_dir, "x264_2pass.log"))
os.rmdir(temp_dir)