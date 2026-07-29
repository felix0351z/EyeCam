import os.path
import time

import cv2 as cv
import yaml

import drawer
from analyzer import Analyzer
from camera import OpenCvCameraSource
from yolo.yolo import YOLO


class EyeCam:
    FPS_AVG_MEASURE_TIME = 10

    def __init__(self):
        """
        Initialize the main program
        """

        config_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        config = yaml.safe_load(open(config_path))
        self.analyzer = Analyzer()
        self.camera = OpenCvCameraSource()
        self.yolo = YOLO()

        self.pipeline = self.yolo.build_pipeline(config)

        self.fps_counter = 0
        self.fps = 0
        self.time_start = None

    def run(self):
        """
        Run the main program
        """
        self.time_start = time.time()

        while True:
            # 1. Read camera input
            frame = self.camera.read()

            # 2. Measure FPS
            self._measure_fps()
            drawer.draw_label(frame, f"FPS: {self.fps}", x=10, y=10)

            # 3. Yolo processing
            detections = self.pipeline.process(frame)
            drawer.draw(detections)

            # 4. Draw results
            drawer.draw_zones(frame)

            # 5. Send results to analyzer
            #self.analyzer.send(self.detection.get_percentages())

            # 5. Show results
            cv.imshow("Eye Cam", frame)

            # End the loop if the key 'Q' was pressed
            if cv.waitKey(1) == ord('q'):
                break

        # Stop the program
        cv.destroyAllWindows()

    def _measure_fps(self):
        self.fps_counter += 1
        if self.fps_counter % self.FPS_AVG_MEASURE_TIME == 0:
            time_end = time.time()
            self.fps = self.FPS_AVG_MEASURE_TIME / (time_end - self.time_start)
            self.time_start = time.time()


# Entrypoint of the application.
while __name__ == "__main__":
    EyeCam().run()