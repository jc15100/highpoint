import numpy as np
import os
import time
import cv2
import sys

import logging
logging.basicConfig()
logger = logging.getLogger('django')
logger.addHandler(logging.StreamHandler(sys.stdout))

from .core.video import Video
from .segmentation.segmenter import MatchSegmenter
from .gpt.openai_vision import OpenAIVisionProcessor

class RacquetSportsMLService:
    openAIProcessor = OpenAIVisionProcessor()

    def check_supported_sport(self, video_path) -> bool:
        video = Video(video_path)
        query="""Please answer with Yes or No. Only answer Yes if you are very confident. Does the image contain people playing the sport of padel, pickleball or tennis?"""
        check = self.openAIProcessor.run_check(video, query, frames_to_check=3)
        video.release()

        return check

    def run_processing(self, video_path, output_path) -> {}:
        logger.info("Video processing started.")
        video = Video(video_path)

        # (1) Use GPT model to extract smashes & any other critical metadata
        smashes = self.extract_smashes(video, self.openAIProcessor)
        smashes_videos_paths = video.extract_subvideos(smashes, video.fps*2, "smash-", output_path)

        # (2) Segment the game into points, return longest point as highlight
        group_highlight = self.extract_group_highlight(video, MatchSegmenter(plotting=False))
        group_highlight_video_path = video.extract_subvideo(start_frame=group_highlight[0], end_frame=group_highlight[1], name="highlight-", output_path=output_path)
        
        video.release()
        logger.info("Video processing finished.")

        return {
            "smashes": smashes_videos_paths, 
            "group_highlight": group_highlight_video_path,
            "supported" : True
            }

    def extract_smashes(self, video, gpt_vision: OpenAIVisionProcessor):
        logger.info("Trying to extract smashes.")

        query = """Please answer with Yes or No. Only answer Yes if you are very confident. You will be shown an image of a game of padel, with 4 players playing doubles. 
A smash in padel is an aggressive overhead shot to finish the point. Is there any player in the image who is performing a smash?"""
        smashes = gpt_vision.process_video(video, query)
        return smashes
    
    def extract_group_highlight(self, video, segmenter: MatchSegmenter):
        logger.info("Trying to extract group highlight.")

        points = segmenter.segment(video)

        print("Key segments " + str(points))
        # find longest point & return as group highlight
        longest_duration = 0
        longest_point = (0, video.fps)

        for point in points:
            current_duration = point[1] - point[0]
            if current_duration > longest_duration:
                longest_duration = current_duration
                longest_point = point

        # return start of point
        return longest_point
