from core.optical_flow import OpticalFlow
import cv2
import numpy as np
import matplotlib.pyplot as plt

'''
Segments a sports match video into points
'''
class Segmenter:
    def __init__(self) -> None:
        self.flow = OpticalFlow()
        self.plotting = False
    
    def segment(self, frame_files):
        print("Starting segmentation")
        old_frame_file = frame_files[0]
        old_frame = cv2.imread(old_frame_file)

        if self.plotting == True:
            hsv = np.zeros_like(old_frame)
            hsv[..., 1] = 255

        old_frame = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)

        flows_sums = []
        for frame in frame_files[1:]:
            current_frame = cv2.imread(frame)
            current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            flow = self.flow.calculate_dense(old_frame, current_frame)

            # sum all vectors contained in the array flow
            flow_sum = np.sum(flow)
            flows_sums.append(flow_sum)

            old_frame = current_frame
            if self.plotting == True:
                # get vector magnitude and angle
                mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                # represent angle via hue
                hsv[..., 0] = ang*180/np.pi/2
                # represent magnitude as value
                hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)

                bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                cv2.imshow('frame2', bgr)
                k = cv2.waitKey(30) & 0xff
                if k == 27:
                    break
        
        if self.plotting == True:
            plt.plot(flows_sums, color = 'blue')
