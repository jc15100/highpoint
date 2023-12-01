import sys
import os

sys.path.append('/Users/juancarlosgarcia/Projects/highpoint/ml/pipeline/')

from highlights.summary import Summary
from core.video import Video
from segmentation.segmenter import Segmenter

from os import listdir
import os
from os.path import isfile, join
import cv2

class Engine:
    def __init__(self):
        self.ready = True
    
    def process(self, video_path):
        self.videopath = video_path
        print("Pipeline started ⚙️")

        video = Video(video_path)
        segmenter = Segmenter(plotting=False)    
        segmenter.segment(video)

        video.release()
        print("Pipeline done ✅")
        
        