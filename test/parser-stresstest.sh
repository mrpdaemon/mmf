#!/bin/bash

find /mnt/raid/nas/video -type f |while read file
do
   ../src/vidparse.py "$file"
done