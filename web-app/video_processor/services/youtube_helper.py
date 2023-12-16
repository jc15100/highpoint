import os
from pytube import YouTube

class YoutubeHelper:
    
    def download_link(self, url, output_path):
        yt = YouTube(url)
        yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(output_path=output_path, filename="temp.mp4")
        video_path = output_path + "/temp.mp4"

        print("Video downloaded at " + str(video_path))
        return video_path