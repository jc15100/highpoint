import numpy as np
import cv2 as cv

'''
Class provides two methods to compute optical flow: (1) sparse optical flow via Lukas-Kanade and (2) dense optical flow via Gunnar Farneback.
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
        return (p1, st, err)
    
    def calculate_dense(self, old_frame, frame):
        # Algorithm specific parameters see https://www.diva-portal.org/smash/get/diva2:273847/FULLTEXT01.pdf
        # 0.5 is image scale for each pyramid, 0.5 is classic pyramid where each layer is twice smaller
        # 3 is number of levels in pyramid 
        # 15 is averaging window size; bigger more robust and can pick up fast motion
        # 3 is number of iterations
        # 5 is poly n, size of the pixel neighborhood; 5 is typical value
        # 1.2 is poly sigma, standard deviation of Gaussian; 1.2 standard for n = 5
        # 0 flags, all off.
        flow = cv.calcOpticalFlowFarneback(old_frame, frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        return flow
