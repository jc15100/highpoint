import cv2
import os

# YOLOV8, ultralytics has commercial license available. Can reconsider & use an equivalent opensource version.
from ultralytics import YOLO

class YOLOStep:
    def __init__(self, video_path):
        self.model = YOLO('yolov8n.pt')

    def predict(self, frame):
        results = self.model(frame)
        return results
    
    def track(self, frame):
        results = self.model.track(frame, persist=True)

        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        print("boxes " + boxes)
        print("track ids" + track_ids)

        return results