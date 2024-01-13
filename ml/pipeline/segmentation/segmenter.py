import cv2
import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import argrelmin
from PIL import Image

from ..core.yolo import YOLOStep
from ..core.optical_flow import OpticalFlow
from ..core.csv import CSVHelper
from ..core.video import Video

'''
Segments a sports match video into points
'''
class MatchSegmenter:
    scale_factor = 0.1

    def __init__(self, plotting) -> None:
        self.flow = OpticalFlow()
        self.plotting = plotting
        self.csv = CSVHelper()
        self.filename = "flows.csv"
        self.yolo = YOLOStep()

        # plotting variables
        self.ax = []
        self.hsv = []

        # segmentation parameters
        self.order = 400
        self.convolve_window = 200
    
    '''
    Segments a Video object in memory. 
    Computes optical flow for the video, then computes relative minima with an order = 500;
    points are estipulated to be parts in between local minima.
    '''
    def segment(self, video: Video):
        flows = None#self.csv.loadDictionary(self.filename)

        if flows is not None:
            print("Optical flow already computed for video, segmenting")
            if self.plotting == True:
                plt.plot(flows[1])
                plt.show()
        else:
            flows_per_player, player_frames = self.detection_flow(video, YOLOStep.person_name)
            # use player with id=1 for segmentation
            if 1 in flows_per_player:
                flows = flows_per_player[1]
            else:
                flows = []

        if len(flows) > 0:
            minima = argrelmin(flows, order=self.order)[0]
            print("Computed minima: " + str(minima))

            if len(minima) == 0:
                print("No minima, setting to first")
                minima = [flows[0]]

            # find key frames
            max_frame_count = video.get_frame_count()
            keyframes_points = []
            for idx, min in enumerate(minima):
                start_frame = min
                if idx+1 < len(minima):
                    end_frame = minima[idx+1]
                else:
                    end_frame = max_frame_count
                
                keyframes_points.append((start_frame, end_frame))

            return {'keyframes': keyframes_points,
                    'player_speeds': flows_per_player,
                    'player_frames': player_frames}
        else:
            return {}

    '''
    Computes speed for a detected object in a Video object (OpenCV VideoCapture) in memory.
    Use this method if process memory is not a concern or video is less than 10GB.
    '''
    def detection_flow(self, video: Video, object_class_name):
        print("Running YOLO to detect players.")
        
        boxes_per_player = {}
        player_frames = []

        while True:
            current_frame = video.read_frame()

            if current_frame is not None:
                frame_small = cv2.resize(current_frame, (0, 0), fx = self.scale_factor, fy = self.scale_factor)
                # call YOLO and extract detections
                results = self.yolo.track(frame_small)
                
                if self.plotting == True:
                    annotated_frame = results[0].plot()
                    # Display the annotated frame
                    cv2.imshow("YOLOv8 Inference", annotated_frame)

                    # Break the loop if 'q' is pressed
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                
                for result in results:
                    for box in result.boxes:
                        if box.id is not None and result.names is not None:
                            id = int(box.id[0].numpy())
                            class_value = int(box.cls[0].numpy())
                            class_name = result.names[class_value]

                            if class_name == object_class_name:
                                # extract top left corner (x, y)
                                x = box.xyxy[0][0].numpy()
                                y = box.xyxy[0][1].numpy()
                                
                                # get width and height to extract player frames
                                w = box.xywh[0][2].numpy()
                                h = box.xywh[0][3].numpy()

                                print("id " + str(id) + " class " + str(class_name) + " x " + str(x) + " y " + str(y))

                                if id not in boxes_per_player:
                                    boxes_per_player[id] = [(x ,y)]

                                    # multiply each value by scale (image was downsized when processed)
                                    player_frame = current_frame[int(y*(1/self.scale_factor)):int(y*(1/self.scale_factor))+int(h*(1/self.scale_factor)), 
                                                                 int(x*(1/self.scale_factor)):int(x*(1/self.scale_factor))+int(w*(1/self.scale_factor))]
                                    if self.plotting == True:
                                        cv2.imshow('id ' + str(id), player_frame)
                                    
                                    player_frames.append(player_frame)
                                else:
                                    boxes_per_player[id].append((x, y))
            else:
                print("Done with frames, exiting YOLO loop")
                break
        
        print("Finished detection_flow with %d boxe(s) out of %d frame(s)" % (len(boxes_per_player),video.get_frame_count()))
        print("Extracted %d player frames (4 expected) " % len(player_frames))

        if len(boxes_per_player) > 0:
            # compute approx. speeds
            frame_interval = 1/video.get_frame_rate()
            
            speeds_per_player = {}
            for player, boxes in boxes_per_player.items():
                speeds = self._object_speed(boxes, frame_interval)

                #store raw speeds in map
                speeds_per_player[player] = speeds
                
                if len(speeds) > 0:
                    # convolve the 1D array of speeds
                    speeds = np.convolve(speeds, np.ones(self.convolve_window)/self.convolve_window, mode='valid')

            # save to CSV for later
            self.csv.saveDictionary(speeds_per_player, self.filename)

            if self.plotting == True:
                # plot one of the speeds
                plt.plot(speeds_per_player[1])
                plt.show()

            return (speeds_per_player, player_frames)
        else:
            return ()

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

        if self.plotting == True:
            plt.plot(flows_sums, color = 'blue')
            plt.show()

        return (frame_segments, flows_sums)
    
    # MARK: Private methods

    def _object_speed(self, positions, time_interval):
        speeds = []
        for i in range(1, len(positions)):
            displacement = np.subtract(positions[i], positions[i-1])
            distance = np.linalg.norm(displacement)
            speed = distance / time_interval
            speeds.append(speed)

        return np.array(speeds)

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
        frame = cv2.resize(frame, (0, 0), fx = self.scale_factor, fy = self.scale_factor)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame