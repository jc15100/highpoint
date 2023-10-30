import numpy as np
import cv2 as cv

'''
Class provides 2 methods to compute optical flow: (1) sparse optical flow via Lukas-Kanade and (2) dense optical flow via Gunnar Farneback.
See https://docs.opencv.org/3.4/d4/dee/tutorial_optical_flow.html for details
'''
class OpticalFlow:
    def __init__(self) -> None:
        self.lk_params = dict( 
            winSize = (15, 15), 
            maxLevel = 2,
            criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        
    def calculate_sparse(self, old_frame, frame, features): 
        p1, st, err = cv.calcOpticalFlowPyrLK(old_frame, frame, features, None, **self.lk_params)
    
    def calculate_dense(self, old_frame, frame):
        # define what each number below means
        flow = cv.calcOpticalFlowFarneback(old_frame, frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
