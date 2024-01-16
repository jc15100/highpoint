import os
from pytube import YouTube

class YoutubeHelper:
    
    def download_link(self, url, output_path):
        print("Downloading video from " + str(url))
        try:
            yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
            print("About to download")
            yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(output_path=output_path, filename="temp.mp4")
            video_path = output_path + "/temp.mp4"

            print("Video downloaded at " + str(video_path))
            return video_path
        except Exception as e:
            print("Failed to download youtube link with error " + str(e))
            return None