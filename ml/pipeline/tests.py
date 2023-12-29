import unittest
from segmentation.segmenter import MatchSegmenter
from core.video import Video
from core.yolo import YOLOStep

class TestSegmenter(unittest.TestCase):
    testVideoPath = "/Users/juancarlosgarcia/Projects/video_tests/test-video-shortest.mp4"

    # def test_detection_flow(self):
    #     test_video = Video(TestSegmenter.testVideoPath)
    #     segmenter = MatchSegmenter(plotting=True)

    #     flows = segmenter.detection_flow(test_video, YOLOStep.person_name)
    #     self.assertTrue(len(flows) > 0)
    
    def test_segment(self):
        test_video = Video(TestSegmenter.testVideoPath)
        segmenter = MatchSegmenter(plotting=True)

        results_dict = segmenter.segment(video=test_video)
        self.assertTrue(results_dict.__contains__('keyframes'))
        self.assertTrue(results_dict.__contains__('player_speeds'))
        self.assertTrue(results_dict.__contains__('player_frames'))
        self.assertTrue(len(results_dict['player_speeds']) > 0)
        self.assertTrue(len(results_dict['player_frames']) > 0)

if __name__ == '__main__':
    unittest.main()