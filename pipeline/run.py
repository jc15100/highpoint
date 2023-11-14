# -*- coding: utf-8 -*-
import numpy as np
from os import listdir
import os
from os.path import isfile, join
import cv2
import argparse

from highlights.summary import Summary
from core.video import Video
from segmentation.segmenter import Segmenter

def pipeline(video_path, output_path, output_filename):
    print("Pipeline started ⚙️")

    # (1) Initialize video
    video = Video(video_path)

    # (1.1) Generate all video frames, if not already done.
    #frames_files = video.video_to_frames(output_path, already_done=True)

    summary = Summary(video_path=video_path)
    #frames_selected = summary.highlights(frames_files, boundary=0.5, skip=True)

    segmenter = Segmenter(plotting=False)    
    segmenter.segment(video)

    video.release()
    print("Pipeline done ✅")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="pipeline", description="Runs the video processing pipeline.")
    parser.add_argument('--input-video')
    parser.add_argument('--output-path')
    parser.add_argument('--output-name')

    args = parser.parse_args()
    pipeline(video_path=args.input_video, output_path=args.output_path, output_filename=args.output_name)
