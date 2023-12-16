import sys
import os

from ml.pipeline.service import RacquetSportsMLService

from os import listdir
import os
from os.path import isfile, join
import cv2

class Engine:
    def __init__(self):
        self.ready = True
    
    def process(self, video_path, output_path):
        service = RacquetSportsMLService()

        # first check it's a supported sport video
        supported = service.check_supported_sport(video_path)

        print("Video of supported sport? " + str(supported))

        if not supported:
            results = {'supported': False}
        else:
            results = service.run_processing(video_path, output_path)
            #results = {'smashes': ['/media/smash-0.mp4', '/media/smash-200.mp4'], 'group_highlight': "/media//highlight-0.mp4"}
        
        return results
        
        