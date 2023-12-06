
import os
from openai import OpenAI
import base64
import cv2

# API key: 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

class GPTProcessor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.getenv("openaikey"))

    def process(self, frame):
        query = """Please answer with Yes or No. Only answer Yes if you are very confident. You will be shown an image of a game of padel, with 4 players playing doubles. 
A smash is defined as a overhead hit of the ball with the racquet, usually very strongly.
Is there any player near the net who is performing a smash, about to perform it or looks like they recently performed a smash?"""
        
        self.process_query(frame, query)
    
    def process_query(self, frame, query):
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
        print(result)

        return result
    