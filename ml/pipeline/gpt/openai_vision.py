
import os
from openai import OpenAI
import base64
import cv2
import time

# API key: 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

class OpenAIVisionProcessor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("openaikey"))
    
    def run_check(self, video, query, frames_to_check) -> bool:
        check_done = False
        check_count = 0
        frame_id = 0

        while not check_done:
            frame = video.read_frame_every(video.fps)

            result = self.process_frame_with_query(frame, query)
            check_done = result.__contains__("Yes")
            check_count +=1
            print("Checking frame " + str(frame_id) + " for supported sport " + str(check_done))
            frame_id += video.fps

            if check_count >= frames_to_check:
                break
        
        return check_done

    def process_video(self, video, query):
        skip_count = 0
        frame = video.read_frame_every(skip_count)

        start_frames_ids = []
        # only find 2 smashes to save on GPT costs
        while frame is not None and len(start_frames_ids) < 2:
            start_time = time.time()
            result = self.process_frame_with_query(frame, query)
            print("process() took %s seconds" % (time.time() - start_time))
            print("Processed %s frame with result %s" % (skip_count, result))
                
            if result.__contains__("Yes"):
                start_frames_ids.append(skip_count)

            skip_count+= int(video.fps)
            print("Reading frame…")
            frame = video.read_frame_every(skip_count)

        print(start_frames_ids)
        return start_frames_ids
    
    def process_frame_with_query(self, frame, query) -> str:
        _, buffer = cv2.imencode(".jpg", frame)
        encoded_base64_string = base64.b64encode(buffer).decode('utf-8')
        image_base64 = f"data:image/jpeg;base64,{encoded_base64_string}"

        print("Creating GPT message")
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
        print("Received GPT response")
        return result
    