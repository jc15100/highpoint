# -*- coding: utf-8 -*-
import numpy as np
from os import listdir
import os
from os.path import isfile, join
import cv2
import argparse
import time

from service import RacquetSportsMLService

def pipeline(video_path, output_path, output_filename):
    print("Pipeline started ⚙️")

    service = RacquetSportsMLService()
    results = service.run_processing(video_path, output_path)
    
    print("Pipeline done ✅")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="pipeline", description="Runs the video processing pipeline.")
    parser.add_argument('--input-video')
    parser.add_argument('--output-path')
    parser.add_argument('--output-name')

    args = parser.parse_args()
    pipeline(video_path=args.input_video, output_path=args.output_path, output_filename=args.output_name)
