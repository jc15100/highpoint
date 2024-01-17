import unittest
from segmentation.segmenter import MatchSegmenter
from core.video import Video
from core.yolo import YOLOStep
import cv2

class Tests(unittest.TestCase):
    testVideoPath = "/Users/juancarlosgarcia/Projects/video_tests/test-video-shortest.mp4"
    testVideoPath2 = "/Users/juancarlosgarcia/Projects/video_tests/test_pickleball.mp4"
    testVideoPath3 = "/Users/juancarlosgarcia/Projects/video_tests/test-tennis.mp4"

    def test_detection_flow(self):
        test_video = Video(Tests.testVideoPath)
        segmenter = MatchSegmenter(plotting=True)

        flows = segmenter.detection_flow(test_video, YOLOStep.person_name)
        self.assertTrue(len(flows) > 0)
    
    def test_segment(self):
        test_video = Video(Tests.testVideoPath)
        segmenter = MatchSegmenter(plotting=True)

        results_dict = segmenter.segment(video=test_video)
        self.assertTrue(results_dict.__contains__('keyframes'))
        self.assertTrue(results_dict.__contains__('player_speeds'))
        self.assertTrue(results_dict.__contains__('player_frames'))
        self.assertTrue(len(results_dict['player_speeds']) > 0)
        self.assertTrue(len(results_dict['player_frames']) > 0)

    def test_yolo(self):
        test_video = Video(Tests.testVideoPath)
        test_video2 = Video(Tests.testVideoPath2)
        test_video3 = Video(Tests.testVideoPath3)
        yolo = YOLOStep()

        #yolo.process_video(test_video)
        #yolo.process_video(test_video2)
        yolo.process_video(test_video3)

if __name__ == '__main__':
    unittest.main()