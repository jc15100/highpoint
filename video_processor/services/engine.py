import sys
import os

from ml.pipeline.service import RacquetSportsMLService

class Engine:
    def __init__(self):
        self.ready = True
    
    def process(self, video_path, output_path):
        service = RacquetSportsMLService()

        # first check it's a supported sport video
        supported = service.check_supported_sport(video_path)

        print("Supported sport? " + str(supported))

        if not supported:
            results = {'supported': False}
        else:
            # results = service.run_processing(video_path, output_path)
            results = {'smashes': ['/Users/juancarlosgarcia/Projects/highpoint/media/smash-433.mp4'], 'group_highlight': '/Users/juancarlosgarcia/Projects/highpoint/media/highlight-88.mp4', 'player_speeds': '{"1": [14.353446312598534, 10.235220283180563, 4.411978381020682, 23.799477280913056, 13.86634447238781, 19.95247501236099, 1.8072990955529988,2950.1304664573704, 2845.917662659606, 2837.8395743660635, 12.939969500104386, 53.10363702840738, 24.360579686922268, 46.34119413949392, 2574.9247700541646, 2507.9161256224243, 62.403483586116025, 152.22352701467233, 2234.07512897259, 23.964212967322897, 11.711265002335463, 15.003789554942736, 15.368503885907487, 13.389863393880745, 1748.8128250533643, 59.06992025308675, 69.44596588790237, 1569.2047210601897, 6.5], “2”: [2565.1064023866757]}', 'player_frames': ['/Users/juancarlosgarcia/Projects/highpoint/media/frame_0000.png', '/Users/juancarlosgarcia/Projects/highpoint/media/frame_0001.png', '/Users/juancarlosgarcia/Projects/highpoint/media/frame_0002.png', '/Users/juancarlosgarcia/Projects/highpoint/media/frame_0003.png', '/Users/juancarlosgarcia/Projects/highpoint/media/frame_0004.png'], 'supported': True}
        return results
        
        