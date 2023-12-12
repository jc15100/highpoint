
import os
from openai import OpenAI
import base64
import cv2
import time
from ..core.csv import CSVHelper

# API key: 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

class OpenAIVisionProcessor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("openaikey"))
        self.keyframes_file = "keyframes_file"
        self.csv = CSVHelper()
    
    def process_video(self, video, query):
        keyframes = self.csv.csvToArray(self.keyframes_file)

        if keyframes is not None:
            print("Key frames already computed, returning")
            return keyframes
        else:
            skip_count = 0
            frame = video.read_frame_every(skip_count)

            start_frames_ids = []
            while frame is not None:
                start_time = time.time()
                result = self.process_frame_with_query(frame, query)
                print("process() took %s seconds" % (time.time() - start_time))
                print("Processed %s frame with result %s \n" % (skip_count, result))
                
                if result.__contains__("Yes"):
                    start_frames_ids.append(skip_count)

                skip_count+= int(video.fps)
                frame = video.read_frame_every(skip_count)

            print(start_frames_ids)
            self.csv.saveArrayToCSV(start_frames_ids, self.keyframes_file)

        return start_frames_ids
    
    def process_frame_with_query(self, frame, query) -> str:
        _, buffer = cv2.imencode(".jpg", frame)
        encoded_base64_string = base64.b64encode(buffer).decode('utf-8')
        image_base64 = f"data:image/jpeg;base64,{encoded_base64_string}"

        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": query
                         },
                         {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64,
                                "detail": "low"
                            }
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        result = response.choices[0].message.content
        return result
    