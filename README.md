MMF
=======

MMF (Mark's media framework) consists of a bunch of scripts that use ffmpeg, mediainfo and neroaacEnc to transcode video for different target devices.

Usage
---------
The player.py application is a frontend for mplayer that parses the input file and passes the right parameters to take advantage of VDPAU acceleration. Useful if you have an nvidia card since mplayer does NOT take advantage of video decoding offload by default.

transcode.py is an ffmpeg frontend that can transcode an input video into a format suitable for the specified target device. Currently the codebase includes target specs for a few devices like the Motorola Xoom, Apple iPhone/iPad, Samsung/Google Nexus S and Roku XDS streaming player, pretty much all using H.264/AAC muxed into mp4. 

TODO
---------
* Proper build/install support
* Support for running transcode.py in Windows
* Multiple input file support.
* Multiple audio stream handling on input files (interactive mode or cmdline for selection)
* Fix stream mapping to not be hardcoded.
* Batching job creation support.
* Add support for interlaced output.
* Implement different audio/video codec support for output.