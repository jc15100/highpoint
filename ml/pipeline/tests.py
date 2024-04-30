import unittest
from segmentation.segmenter import MatchSegmenter
from core.video import Video
from core.yolo import YOLOStep
import time
import cv2

class Tests(unittest.TestCase):
    testVideoPath = "/Users/juancarlosgarcia/Projects/video_tests/test-video-shortest.mp4"
    testVideoPath2 = "/Users/juancarlosgarcia/Projects/video_tests/test_pickleball.mp4"
    testVideoPath3 = "/Users/juancarlosgarcia/Projects/video_tests/test-tennis.mp4"
    
    def test_segment(self):
        test_video = Video(Tests.testVideoPath)
        segmenter = MatchSegmenter(plotting=False)

        start = time.time()
        results_dict = segmenter.segment(video=test_video)
        end = time.time()
        print("Segmenter Elapsed Time: {}".format(end - start))

        self.assertTrue(results_dict.__contains__('keyframes'))
        self.assertTrue(results_dict.__contains__('player_speeds'))
        self.assertTrue(results_dict.__contains__('player_frames'))
        self.assertTrue(len(results_dict['player_speeds']) > 0)
        self.assertTrue(len(results_dict['player_frames']) > 0)
        print(results_dict['player_speeds'])

    def _test_video_extract(self):
        test_video = Video(Tests.testVideoPath)
        test_frame_indices = [5, 10, 15, 25, 56]
        test_frame_window = 100
        for frame_idx in test_frame_indices:
            end_idx = min(frame_idx + test_frame_window, test_video.get_frame_count())

            start_time = time.time()
            video_in_memory = test_video.extract_subvideo(frame_idx, end_idx)
            end_time = time.time()
            print("Extracting subvideo took %d (s)" % (end_time - start_time))

    def _test_yolo(self):
        test_video = Video(Tests.testVideoPath)
        yolo = YOLOStep()
        yolo.process_video(test_video)

if __name__ == '__main__':
    unittest.main()