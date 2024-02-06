import cv2
import os
import numpy as np

# YOLOV8, ultralytics has commercial license available. Can reconsider & use an equivalent opensource version.
from ultralytics import YOLO

class YOLOStep:
    # Constants used to extract key elements from YOLO results
    ball_name = 'sports ball'
    person_name = 'person'
    scale_factor = 0.3
    model = YOLO('yolov8n.pt')

    def predict(self, frame):
        results = YOLOStep.model(frame)
        return results
    
    def track(self, frame):
        results = YOLOStep.model.track(frame)
        return results
    
    def process_video(self, video):
        count = 0
        while True:
            current_frame = video.read_frame()
            if current_frame is not None:
                frame_small = cv2.resize(current_frame, (0, 0), fx = self.scale_factor, fy = self.scale_factor)
                results = self.track(frame_small)
                annotated_frame = results[0].plot()
                path = "frame-"+str(count)+".png"
                cv2.imwrite(path, annotated_frame)
                count+=1
            else:
                break
        
        frames_directory = '.'

        # Get the list of JPEG files in the directory
        frames = [f for f in os.listdir(frames_directory) if f.endswith('.png')]

        # Sort the files to maintain the correct order
        frames.sort()

        # Get the first frame to obtain image dimensions
        first_frame_path = os.path.join(frames_directory, frames[0])
        first_frame = cv2.imread(first_frame_path)
        height, width, layers = first_frame.shape

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter("test.mp4", fourcc, 30.0, (width, height))  

        # Iterate through each JPEG file and write it to the video file
        for frame in frames:
            frame_path = os.path.join(frames_directory, frame)
            frame = cv2.imread(frame_path)
            video_writer.write(frame)

        # Release the VideoWriter object
        video_writer.release()