# -*- coding: utf-8 -*-
import numpy as np
from os import listdir
import os
from os.path import isfile, join
import cv2
import argparse

from highlights.summary import Summary
from core.yolo import YOLOStep
from core.tracker import Tracker
from core.video import Video
from highpoint.segmenter import Segmenter

def pipeline(video_path, output_path, output_filename):
    print("Pipeline started ⚙️")

    # (1) Turn video into frames files
    video = Video(video_path)

    # (1.1) Generate all video frames, if not already done.
    frames, frames_files = video.video_to_frames(output_path, already_done=False)

    # (2) Initialize Summary step
    summary = Summary(video_path=video_path)

    # Test segmenter
    segmenter = Segmenter()
    segmenter.segment(frames)

    return 
    # (3) Detect highlights (optional)
    frames_selected = summary.highlights(frames_files, boundary=0.5, skip=True)

    # (4) Setup YOLO
    yolo = YOLOStep(video_path=video_path)

    # (4.2) Get frame files & height, width
    frame_paths, height, width = video.frame_paths(output_path=output_path)

    # (4.3) Adding frames to video & run YOLO on the frame
    decorated_frames = []
    for i in range(len(frame_paths)):
        if frames_selected[i]:
            frame_file = frames_files[i]
            frame_image = cv2.imread(frame_file)

            # get bounding boxes from YOLO
            results = yolo.track(frame_image)

            annotated_frame = video.decorate(results)
            decorated_frames.append(annotated_frame)
    
    # (5) Store final video
    video.frames_to_video(frames=decorated_frames, height=height, width=width, output_video_path=output_filename)

    print("Pipeline done ✅")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="pipeline", description="Runs the video processing pipeline.")
    parser.add_argument('--input-video')
    parser.add_argument('--output-path')
    parser.add_argument('--output-name')

    args = parser.parse_args()
    pipeline(video_path=args.input_video, output_path=args.output_path, output_filename=args.output_name)
