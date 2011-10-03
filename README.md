MMF
=======

MMF (Mark's media framework) consists of a bunch of scripts that use ffmpeg, mediainfo and neroaacEnc to transcode video for different target devices.

Usage
---------
The mmfplay application is a frontend for mplayer that parses the input file and passes the right parameters to take advantage of VDPAU acceleration. Useful if you have an nvidia card since mplayer does NOT take advantage of video decoding offload by default.

mmfxcode is an ffmpeg frontend that can transcode an input video into a format suitable for the specified target device. Currently the codebase includes target specs for a few devices like the Motorola Xoom, Apple iPhone/iPad, Samsung/Google Nexus S and Roku XDS streaming player, pretty much all using H.264/AAC muxed into mp4. 

TODO
---------
* Support copy audio codec
* Add target for 1080p-mp4-h264-copy
* Support "same" for audio sample rate
* Improve usage() documentation
* Implement split output support via MAX_OUTPUT_DURATION
* Add target for YouTube
* Proper build/install support
* Support for running mmfxcode in Windows
* Multiple audio stream handling on input files (interactive mode or cmdline for selection)
* Fix stream mapping to not be hardcoded.
* Batching job creation support.
* Implement different audio/video codec support for output.