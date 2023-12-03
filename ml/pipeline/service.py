import numpy as np
import os
import cv2

from highlights.summary import Summary
from core.video import Video
from segmentation.segmenter import Segmenter

class MLService:

    def run_processing(self, video_path):
        print("Video processing started.")
        # (1) Initialize video
        video = Video(video_path)

        # (1.1) Generate all video frames, if not already done.
        #frames_files = video.video_to_frames(output_path, already_done=True)

        summary = Summary(video_path=video_path, model_path= "../trained_model/split0/")
        #frames_selected = summary.highlights(frames_files, boundary=0.5, skip=True)

        segmenter = Segmenter(plotting=False)    
        segmenter.segment(video)

        video.release()

        print("Video processing finished.")
