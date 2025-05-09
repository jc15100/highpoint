import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import av
import io

class Video:
    def __init__(self, video_path, debug=False):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        # Check video
        if not self.cap.isOpened():
            print(f"Error to open the video in {video_path}")
            exit()
        # Output video stats
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.debug = debug
        print("Loaded video with fps %s" % self.fps)

    def get_frame_count(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    def get_duration(self):
        return int(self.get_frame_count()/self.get_frame_rate())

    def get_frame_width(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    def get_frame_height(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def get_frame_rate(self):
        return self.cap.get(cv2.CAP_PROP_FPS)

    def read_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            return None
    
    def read_frame_every(self, skip_count):
        frame = self.read_frame()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, skip_count)

        if frame is not None:
            frame = self._downsize_frame(frame)

            if self.debug:
                cv2.imshow(f'frame-{skip_count}', frame)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

        return frame
    
    def extract_frames(self, start, end):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start-1)

        print("Extracting frames from {} to {}".format(str(start), str(end)))
        count = end - start
        subset = []
        frame = self.read_frame()
        while count >= 0 and frame is not None:
            frame = cv2.resize(frame, (0, 0), fx = 0.1, fy = 0.1)
            subset.append(frame)
            count-=1
            frame = self.read_frame()
        print("Done extracting frames.")

        return subset

    def extract_subvideo(self, start_frame, end_frame):
        current_poi = self.extract_frames(start_frame, end_frame)

        height = current_poi[0].shape[0]
        width = current_poi[0].shape[1]

        return self.frames_to_video_in_memory(current_poi, height, width)
    
    def video_to_frames(self, output_path, already_done=False):
        frame_count = 0
        frame_paths = []
        if already_done:
            print("Frames already available at " + output_path)
            frame_paths = [os.path.join(output_path, f) for f in os.listdir(output_path) if f.endswith('.png')]
            frame_paths.sort()
            return frame_paths
        else:
            print("Extracting frames from video 💪🏼")
            # Read and save video frames
            while True:
                ret, frame = self.cap.read()
                
                # if ret is False, the video is ended or an error happened
                if not ret:
                    break
                
                frame_filename = os.path.join(output_path, f"frame_{frame_count:04d}.png")
                cv2.imwrite(frame_filename, frame)
                frame_paths.append(frame_filename)
                frame_count += 1
                print("processed " + str(frame_filename))

        # Closing video
        print(f"Successfully created {frame_count} frames.")
        return frame_paths
    
    def draw_graph(self, data):
        fig, ax = plt.subplots()
        plt.ion()
        plt.show()
        line, = ax.plot(np.arange(data), np.zeros((data,)), c='r', lw=3, alpha=0.8)
        line.set_ydata(data)
        fig.canvas.draw()

    def frame_paths(self, output_path):
        frame_paths = [f for f in os.listdir(output_path) if f.endswith('.png')]

        # Is important sort the names of the frames
        frame_paths.sort()

        # Get resolutions
        first_frame = cv2.imread(os.path.join(output_path, frame_paths[0]))
        height, width, _ = first_frame.shape

        return (frame_paths, height, width)
    
    def frames_to_video_in_memory(self, frames, height, width):
        # Set video settings & write to stream
        output_memory_file = io.BytesIO()
        output = av.open(output_memory_file, 'w', format="mp4")
        stream = output.add_stream('h264', str(int(self.fps)))
        stream.width = width
        stream.height = height
        stream.pix_fmt = 'yuv444p'
        stream.options = {'crf': '17'}

        print("Writing " + str(len(frames)) + " frames of " + str(width) + " by " + str(height))
        for img in frames:
            frame = av.VideoFrame.from_ndarray(img, format='bgr24')
            packet = stream.encode(frame)
            output.mux(packet)
        packet = stream.encode(None)
        output.mux(packet)
        output.close()

        output_memory_file.seek(0)
        size_in_bytes = len(output_memory_file.getbuffer())

        print(f"Size of BytesIO object: {size_in_bytes} bytes")

        # # Write BytesIO from RAM to file, for testing
        # with open("output.mp4", "wb") as f:
        #     f.write(output_memory_file.getbuffer())
        
        return output_memory_file
    
    def frames_to_video(self, frames, height, width, output_video_url):
        # Set video settings
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_video = cv2.VideoWriter(output_video_url, fourcc, self.fps, (width, height))    

        if output_video.isOpened():
            print("Writing " + str(len(frames)) + " frames of " + str(width) + " by " + str(height) + " to the filesystem")
            for frame in frames:
                output_video.write(frame)
            print("Successfully saved video at " + str(output_video_url))
        else:
            print("Failed to save video")
        output_video.release()
    
    def decorate(self, results):
        # plot the bounding boxes for the diferent classes onto the frame
        annotated_frame = results[0].plot()

        # render the tracked skeleton pose
        # print keypoints index number and x,y coordinates
        if results[0].keypoints is not None:
            for idx, kpt in enumerate(results[0].keypoints[0]):
                print(f"Keypoint {idx}: ({int(kpt[0])}, {int(kpt[1])})")
                annotated_frame = cv2.putText(annotated_frame, f"{idx}:({int(kpt[0])}, {int(kpt[1])})", (int(kpt[0]), int(kpt[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
    
        #annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        return annotated_frame
    
    def reset(self):
        print("Resetting video pointer to first frame")
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def release(self):
        self.cap.release()
    
    def _downsize_frame(self, frame):
        frame = cv2.resize(frame, (0, 0), fx = 0.1, fy = 0.1)
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame

if __name__ == '__main__': 
    pass
