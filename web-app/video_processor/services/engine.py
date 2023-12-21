import sys
import os

from ml.pipeline.service import RacquetSportsMLService

class Engine:
    def __init__(self):
        self.ready = True
    
    def process(self, video_path, output_path):
        service = RacquetSportsMLService()

        # first check it's a supported sport video
        supported = True#service.check_supported_sport(video_path)

        print("Supported sport? " + str(supported))

        if not supported:
            results = {'supported': False}
        else:
            #results = service.run_processing(video_path, output_path)
            results = {'supported': True, 'smashes': ['/media/smash-636.mp4', '/media/smash-723.mp4'], 'group_highlight': "/media//highlight-10.mp4", 
                       'player_speeds':"{\"1\": [179.7213347412862, 179.72987851929983, 179.76330296116905, 179.85739903794337], " + 
                       "\"2\": [173.7213347412862, 172.72987851929983, 18.76330296116905, 17.85739903794337], " + 
                       "\"3\": [17.7213347412862, 1.72987851929983, 18.76330296116905, 145.85739903794337]}"}
        
        return results
        
        