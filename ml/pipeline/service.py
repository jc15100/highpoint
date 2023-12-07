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
        smashes = processor.process_video(video)
        
        for frame_idx in smashes:
            current_smash = video.extract_frames(int(frame_idx - video.fps/2), int(frame_idx + video.fps/2))

            height = current_smash[0].shape[0]
            width = current_smash[0].shape[1]

            smash_path = output_path + os.sep + "smash-" + str(frame_idx) + ".mp4"
            video.frames_to_video(current_smash, height, width, smash_path)

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
