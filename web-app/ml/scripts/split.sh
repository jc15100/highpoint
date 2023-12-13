
#!bin/bash

var=$1
if [ "$#" -eq 0 ]; then
    echo "Missing input video path"
    exit 1
fi

# segment_time defines the # of minutes to split a video by
segment_time=5
if [ -z "$2" ]; then
    echo "Missing segment duration, defaulting to 5 mins"
else
    segment_time=$2
fi

# input_video should specify path to .mov video to split
input_video=$1

# step 1: convert .mov to mp4
ffmpeg -i $input_video -vcodec h264 -acodec mp2 intermediate.mp4

# step 2: split into segments
ffmpeg -i intermediate.mp4 -c copy -map 0 -segment_time 00:$segment_time -f segment segment%03d.mp4