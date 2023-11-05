from core.optical_flow import OpticalFlow

'''
Segments a video into points
'''
class Segmenter:
    def __init__(self) -> None:
        self.flow = OpticalFlow()
    
    def segment(self, frames):
        print("Starting segmentation")
        old_frame = frames[0]
        for frame in frames[1:]:
            flow = self.flow.calculate_dense(old_frame, frame)

            print("Flow " + str(flow))
            old_frame = frame
