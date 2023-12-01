import cv2
import os

# YOLOV8, ultralytics has commercial license available. Can reconsider & use an equivalent opensource version.
from ultralytics import YOLO

class YOLOStep:
    # Constants used to extract key elements from YOLO results
    ball_name = 'sports ball'
    person_name = 'person'

    def __init__(self):
        self.model = YOLO('yolov8n.pt')

    def predict(self, frame):
        results = self.model(frame)
        return results
    
    def track(self, frame):
        results = self.model.track(frame)
        return results