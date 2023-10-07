import cv2
import os
import torch
import numpy as np
#from inference.generate_summary import generate_summary
from os import listdir
import glob
import os
from os.path import isfile, join

from layers.summarizer import PGL_SUM
from core.video import Video
from core.frame import Frames

class Summary:
    def __init__(self, video_path):
        self.video_path = video_path
        self.frames = Frames(video_path)
        self.model_path = "trained_model/split0/"
        self.model_file = [f for f in listdir(self.model_path) if isfile(join(self.model_path, f))]
    
        # Create model with paper reported configuration
        self.trained_model = PGL_SUM(input_size=1024, output_size=1024, num_segments=4, heads=8,fusion="add", pos_enc="absolute")
        self.trained_model.load_state_dict(torch.load(join(self.model_path, self.model_file[-1]), map_location=torch.device('cpu')))
    
    '''
    Returns an array of 1 or 0s indicating whether the corresponding frame is to be included or not in summary.
    '''
    def summarize(self, frames, boundary=0.5, skip=False):
        if skip == True:
            # Skip processing and just pick all frames
            all_frames = [1 for n in range(len(frames))]
            print("Skipped summarization step")
            return all_frames
        else:
            # encode frames (calls InceptionV3 to get encodings for each frame)
            print("Running summarization step")
            frames_features = []
            for frame_dir in frames:
                print(frame_dir)
                single_frame_feature = list(self.frames.encode_frame(frame_dir))
                frames_features.append(single_frame_feature)
                print(len(frames_features))

            # uses PGL_SUM model to predict a given frame encoding in terms of "summary" quality
            self.trained_model.eval()
            with torch.no_grad():
                frames_features = torch.Tensor(frames_features)
                scores, _ = self.trained_model(frames_features)  # [1, seq_len]
                scores = scores.squeeze(0).cpu().numpy().tolist()
                
                # Based on scores, pick which frames to include.
                frames_selected = np.where(np.array(scores) > boundary, 1, 0)
                return frames_selected