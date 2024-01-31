import numpy as np
import json
from datetime import datetime

from .core.video import Video
from .segmentation.segmenter import MatchSegmenter
from .gpt.openai_vision import OpenAIVisionProcessor
from .result import HighpointResult
from .core.storage_helper import StorageHelper

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
    
class RacquetSportsMLService:

    def __init__(self, storage_helper: StorageHelper) -> None:
        self.storage_helper = storage_helper
        self.segmenter = MatchSegmenter(plotting=False)
        self.openAIProcessor = OpenAIVisionProcessor()

    def check_supported_sport(self, video_url) -> bool:
        video = Video(video_url)
        query="""Please answer with Yes or No. Only answer Yes if you are very confident. Does the image contain people playing the sport of padel, pickleball or tennis?"""
        check = self.openAIProcessor.run_check(video, query, frames_to_check=3)
        video.release()

        return check

    def run_processing(self, video_url, request) -> {}:
        print("Video processing started.")
        video = Video(video_url)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # (1) Use GPT model to detect smashes & any other critical metadata
        smashes = self.detect_smashes(video, self.openAIProcessor)
        smashes_videos, smashes_videos_urls = self.extract_smashes(user=request.user, 
                                              video=video, 
                                              smashes=smashes, 
                                              window_size=video.fps*2, 
                                              name="smash-",
                                              timestamp=timestamp,
                                              storage_helper=self.storage_helper)

        video.reset()

        # (2) Segment the game into points, return longest point as highlight        
        group_highlight, player_speeds, player_frames, player_frames_urls = self.detect_group_highlight(user=request.user, 
                                                                                    video=video,
                                                                                    segmenter=self.segmenter,
                                                                                    timestamp=timestamp,
                                                                                    storage_helper=self.storage_helper)
        
        group_highlight_video, group_highlight_url = self.extract_group_highlight(user=request.user, 
                                                                  video=video, 
                                                                  start_frame=group_highlight[0], 
                                                                  end_frame=group_highlight[1], 
                                                                  name="highlight-",
                                                                  timestamp=timestamp,
                                                                  storage_helper=self.storage_helper)
        video.release()

        print("Video processing finished.")

        return HighpointResult(
            smashes=smashes_videos,
            smashes_urls=smashes_videos_urls,
            group_highlight=group_highlight_video, 
            group_highlight_url=group_highlight_url,
            player_frames=player_frames,
            player_frames_urls=player_frames_urls, 
            player_speeds=player_speeds, 
            supported=True
        )

    # Private methods

    def extract_smashes(self, user, video: Video, smashes, window_size, name, timestamp, storage_helper: StorageHelper):
        subvideos = []
        subvideos_urls = []
        for frame_idx in smashes:
            start_idx = int(frame_idx - window_size) if (frame_idx - window_size) > 0 else frame_idx
            end_idx = max(int(frame_idx + window_size), video.get_frame_count())
            
            subvideo_bucket_path = storage_helper.get_results_bucket_path(user,  name + str(start_idx) + ".mp4", timestamp)
            subvideo_url = storage_helper.get_signed_url(subvideo_bucket_path, "GET")
            blob = storage_helper.get_blob(subvideo_bucket_path)

            video_in_memory = video.extract_subvideo(start_idx, end_idx)
            blob.upload_from_file(video_in_memory, content_type='video/mp4')

            subvideos.append(subvideo_bucket_path)
            subvideos_urls.append(subvideo_url)
        
        print("Extracted {} subvideos ".format(len(subvideos)))
        return (subvideos, subvideos_urls)

    def detect_smashes(self, video, gpt_vision: OpenAIVisionProcessor):
        print("Trying to extract smashes.")

        query = """Please answer with Yes or No. Only answer Yes if you are very confident. You will be shown an image of a game of padel, with 4 players playing doubles. 
A smash in padel is an aggressive overhead shot to finish the point. Is there any player in the image who is performing a smash?"""
        smashes = gpt_vision.process_video(video, query)
        return smashes
    
    def extract_group_highlight(self, user, video: Video, start_frame, end_frame, name, timestamp, storage_helper: StorageHelper):
        highlight_bucket_path = storage_helper.get_results_bucket_path(user, name + str(start_frame) + ".mp4", timestamp)
        blob = storage_helper.get_blob(highlight_bucket_path)
        highlight_url = storage_helper.get_signed_url(highlight_bucket_path, "GET")
        video_in_memory = video.extract_subvideo(start_frame=start_frame, end_frame=end_frame)
        blob.upload_from_file(video_in_memory, content_type='video/mp4')
        
        return (highlight_bucket_path, highlight_url)

    def detect_group_highlight(self, user, video, segmenter: MatchSegmenter, timestamp, storage_helper: StorageHelper):
        print("Trying to extract group highlight.")

        results_dict = segmenter.segment(video)
        points = results_dict['keyframes']
        print("Key segments " + str(points))
        
        # find longest point & return as group highlight
        longest_duration = 0
        longest_point = (0, video.fps)

        for point in points:
            current_duration = point[1] - point[0]
            if current_duration > longest_duration:
                longest_duration = current_duration
                longest_point = point

        # return longest point & player_speeds
        player_speeds_non_np = {}
        for player, speeds in results_dict['player_speeds'].items():
            player_speeds_non_np[player] = speeds.tolist()

        player_speeds_json = json.dumps(player_speeds_non_np)

        # save frames to storage
        player_frames = results_dict['player_frames']
        player_frames_urls = []
        player_frames_ = []
        for id, player in enumerate(player_frames):
            frame_bucket_path = storage_helper.get_results_bucket_path(user, f"frame_{id:04d}.png", timestamp)
            blob = storage_helper.get_blob(frame_bucket_path)
            frame_url = storage_helper.get_signed_url(frame_bucket_path, "GET")
            
            player_frames_.append(frame_bucket_path)
            player_frames_urls.append(frame_url)
            
            storage_helper.upload_frame(player, blob)

        return (longest_point, player_speeds_json, player_frames_, player_frames_urls)
