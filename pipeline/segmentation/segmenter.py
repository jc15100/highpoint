import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelmin

from core.optical_flow import OpticalFlow
from core.csv import CSVHelper
from core.video import Video

'''
Segments a sports match video into points
'''
class Segmenter:
    def __init__(self, plotting) -> None:
        self.flow = OpticalFlow()
        self.plotting = plotting
        self.csv = CSVHelper()
        self.filename = "flows.csv"

        # plotting variables
        self.ax = []
        self.hsv = []

        # segmentation parameters
        self.order = 500
    
    '''
    Segments a Video object in memory. 
    Computes optical flow for the video, then computes relative minima with an order = 500;
    points are estipulated to be parts in between local minima.
    '''
    def segment(self, video: Video):
        flows = self.csv.csvToArray(self.filename)
        if flows is not None:
            print("Optical flow already computed for video, segmenting")
        else:
            flows = self.video_flow(video)

        minima = argrelmin(flows, order=self.order)[0]
        #print("minima: " + str(minima))

        max_frame_count = video.get_frame_count()
        frames_segments = []
        for idx, min in enumerate(minima):
            start_frame = min
            if idx+1 < len(minima):
                end_frame = minima[idx+1]
            else:
                end_frame = max_frame_count
            
            frames_segments.append((start_frame, end_frame))

        print("segments: " + str(frames_segments))
        for ids, segment in enumerate(frames_segments):
            segment_frames = video.extract_frames(segment[0], segment[1])
            height = segment_frames[0].shape[0]
            width = segment_frames[0].shape[1]

            video.frames_to_video(segment_frames, height, width, "segment-" + str(ids) + ".mp4")

    '''
    Computes optical flow across each frame in a Video object (OpenCV VideoCapture) in memory.
    Use this method if process memory is not a concern or video is less than 10GB.
    '''
    def video_flow(self, video: Video):
        print("Starting optical flow with Video object")
        old_frame = video.read_frame()
        old_frame = self._prepare_frame(old_frame)

        flows_sums = []
        frame_segments = []

        self._debug_plot_init(old_frame)
        
        while True:
            current_frame = video.read_frame()

            if current_frame is not None:
                current_frame = self._prepare_frame(current_frame)

                # calculate flow & sum all vectors contained in the array
                flow = self.flow.calculate_dense(old_frame, current_frame)
                flow_sum = np.sum(flow)
                flows_sums.append(flow_sum)

                print("Flow sum " + str(flow_sum) + ", frame " + str(len(flows_sums)))
                old_frame = current_frame

                self._debug_plot(self.ax, current_frame, flows_sums, flow, self.hsv)
            else:
                break
        
        # convolve the 1D array of sums to smooth out
        flows_sums = np.convolve(flows_sums, np.ones(10)/10, mode='valid')

        # save to CSV for later
        self.csv.saveArrayToCSV(flows_sums, "flows.csv")
        
        if self.plotting == True:
            plt.plot(flows_sums, color = 'blue')
            plt.show()

        return (frame_segments, flows_sums)

    '''
    Computes optical flow across a set of frame files.
    This memory takes longer due to the incurred IO of reading each file.
    Use this method if process memory is a bottleneck, or video is too large that can't be loaded into memory (> 10GB)
    '''
    def frames_flow(self, frame_files):
        print("Starting optical flow with frame files")
        
        old_frame_file = frame_files[0]
        old_frame = cv2.imread(old_frame_file)
        old_frame = self._prepare_frame(old_frame)

        flows_sums = []
        frame_segments = []

        self._debug_plot_init(old_frame)

        for frame in frame_files[1:]:
            current_frame = cv2.imread(frame)
            current_frame = self._prepare_frame(current_frame)

            # calculate dense optical flow & sum all vectors contained in the array
            flow = self.flow.calculate_dense(old_frame, current_frame)
            flow_sum = np.sum(flow)

            flows_sums.append(flow_sum)
            frame_segments.append(frame)

            print("Flow sum " + str(flow_sum) + ", frame " + str(len(flows_sums)))
            old_frame = current_frame
            self._debug_plot(self.ax, current_frame, flows_sums, flow, self.hsv)
            
        
        # convolve the 1D array of sums to smooth out
        flows_sums = np.convolve(flows_sums, np.ones(10)/10, mode='valid')

        # save to CSV for later
        self.csv.saveArrayToCSV(flows_sums, self.filename)

        #if self.plotting == True:
        plt.plot(flows_sums, color = 'blue')
        plt.show()

        return (frame_segments, flows_sums)
    
    # MARK: Private methods

    def _debug_plot_init(self, frame):
        if self.plotting == True:
            plt.ion()
            hsv = np.zeros_like(frame)
            hsv[..., 1] = 255
            self.hsv = hsv

            _, ax = plt.subplots(2,1)
            self.ax = ax

    def _debug_plot(self, axes, current_frame, flows_sums, flow, hsv):
        if self.plotting == True:
            axes[0].imshow(current_frame)
            axes[1].plot(flows_sums)
            plt.draw()
            plt.pause(0.001)

            # get vector magnitude and angle
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            # represent angle via hue
            hsv[..., 0] = ang*180/np.pi/2
            # represent magnitude as value
            hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)

            bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            cv2.imshow('frame', bgr)

    def _prepare_frame(self, frame):
        frame = cv2.resize(frame, (0, 0), fx = 0.1, fy = 0.1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame