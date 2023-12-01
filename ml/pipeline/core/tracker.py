from ultralytics.trackers.utils.kalman_filter import KalmanFilterXYAH

'''
Tracker class will implement a custom tracker for a specified class.
'''
class Tracker:
    def __init__(self, class_to_track):
        self.kalman = KalmanFilterXYAH()
        self.class_to_track = class_to_track
        self.initiated = False
    
    def initiate(self, results):
        if self.initiated:
            return
        bounding_box = self.__extract_class_bounding_box(results)
        self.mean, self.cov = self.kalman.initiate(bounding_box)
        self.initiated = True

    def predict(self, mean, covariance):
        self.mean, self.cov = self.kalman.predict(mean, covariance)

    def update(self, mean, covariance, bounding_box):
        return self.kalman.update(mean, covariance, bounding_box)
    
    def track(self, results):
        self.initiate(results)
        self.predict(self.mean, self.cov)
        bounding_box = self.__extract_class_bounding_box(results)
        self.mean, self.cov = self.update(self.mean, self.cov, bounding_box)

    def __extract_class_bounding_box(self, results):
        return results[1]
