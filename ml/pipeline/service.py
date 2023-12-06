import numpy as np
import os
import time
import cv2

import logging
logging.basicConfig()
logger = logging.getLogger('django')

from highlights.summary import Summary
from core.video import Video
from segmentation.segmenter import Segmenter
from llm.openai_vision import OpenAIVisionProcessor

class MLService:

    def run_processing(self, video_path, output_path) -> []:
        logger.info("Video processing started.")
        video = Video(video_path)

        processor = OpenAIVisionProcessor()
        processor.process_video(video)
        
        return

        # (1.1) Generate all video frames, if not already done.
        #frames_files = video.video_to_frames(output_path, already_done=True)

        #summary = Summary(video_path=video_path, model_path= "../trained_model/split0/")
        #frames_selected = summary.highlights(frames_files, boundary=0.5, skip=True)

        segmenter = Segmenter(plotting=False)    
        segments_paths = segmenter.segment(video, output_path)
        
        logger.debug("# of segments: " + str(len(segments_paths)))
        video.release()
        logger.info("Video processing finished.")

        return segments_paths
