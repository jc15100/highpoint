import numpy as np
import cv2 as cv

'''
Lukas-Kanade method to calculate Optical Flow. 
See https://docs.opencv.org/3.4/d4/dee/tutorial_optical_flow.html for details
'''
class OpticalFlow:
    def __init__(self) -> None:
        self.lk_params = dict( 
            winSize = (15, 15), 
            maxLevel = 2,
            criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        
    def calculate(self, old_frame, frame, features): 
        p1, st, err = cv.calcOpticalFlowPyrLK(old_frame, frame, features, None, **self.lk_params)