import cv2
import tensorflow as tf
import numpy as np
import urllib
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense

class Frames:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Using InceptionV3 model
        self.base_model = InceptionV3(weights='imagenet', include_top=True)
        self.model = Model(inputs=self.base_model.input, outputs=self.base_model.layers[-2].output)
        self.reduced_dimension_layer = Dense(1024, activation='relu')(self.model.output) # Add a Dense layer to reduce the dimension to 1024 
        self.final_model = Model(inputs=self.model.input, outputs=self.reduced_dimension_layer) # Putting all layers in one model

    def read_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            return None

    def show_frame(self, frame, window_name='Frame'):
        cv2.imshow(window_name, frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def encode_frame(self, frame_path):
        img = cv2.imread(frame_path)
        _, buffer = cv2.imencode('.png', img)
        img = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (299, 299))  # Adjusting the size as needed for InceptionV1

        # Preprocess the image to make it compatible with InceptionV3
        img = preprocess_input(img)
        img = np.expand_dims(img, axis=0)

        # Get the deep representation of the frame
        deep_features = self.final_model.predict(img)
        # Now, deep_features contains the deep representations from the 'pool5' layer with dimension D = 1024
        return deep_features[0]
    
    def save_frame(self, frame, output_path):
        cv2.imwrite(output_path, frame)

    def release(self):
        self.cap.release()
