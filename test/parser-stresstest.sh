#!/bin/bash

for i in `find /mnt/raid/nas/video -type f`;do ../src/vidparse.py "$i";done