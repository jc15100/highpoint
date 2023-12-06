
import os
from openai import OpenAI
import base64
import cv2
import time

# API key: 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

class OpenAIVisionProcessor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("openaikey"))

    def process_video(self, video):
        skip_count = 0
        frame = video.read_frame_every(skip_count)

        while frame is not None:
            start_time = time.time()
            result = self.process_frame(frame)
            print("process() took %s seconds" % (time.time() - start_time))
            print("Processed %s frame with result %s \n" % skip_count % result)

            skip_count+= int(video.fps)
            frame = video.read_frame_every(skip_count)

    def process_frame(self, frame) -> str:
        query = """Please answer with Yes or No. Only answer Yes if you are very confident. You will be shown an image of a game of padel, with 4 players playing doubles. 
A smash is defined as a overhead hit of the ball with the racquet, usually very strongly.
Is there any player near the net who is performing a smash, about to perform it or looks like they recently performed a smash?"""
        
        return self.process_frame_with_query(frame, query)
    
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
    