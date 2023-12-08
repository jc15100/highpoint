import sys
import os

sys.path.append('/Users/juancarlosgarcia/Projects/highpoint/ml/pipeline/')

from service import RacquetSportsMLService

from os import listdir
import os
from os.path import isfile, join
import cv2

class Engine:
    def __init__(self):
        self.ready = True
    
    def process(self, video_path, output_path):
        service = RacquetSportsMLService()
        results = service.run_processing(video_path, output_path)
        return results
        
        