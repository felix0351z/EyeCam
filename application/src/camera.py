import sys
import time

import cv2 as cv

from analyzer import Analyzer
from detections.zone_based_detection import ZoneBasedDetection
from settings import EyeCamSettings
from drawer import Drawer, draw_label, draw_zones
from yolo import YOLOv26Model

class EyeCam:

    def __init__(self):
        """
        Initialize the main program
        """

        self.settings = EyeCamSettings()
        self.model = YOLOv26Model(self.settings)
        self.drawer = Drawer(self.settings)
        self.detection = ZoneBasedDetection(self.model.MODEL_SIZE)
        self.analyzer = Analyzer()

        self.cam = cv.VideoCapture(0)
        self.fps_counter = 0
        self.fps = 0

    def run(self):
        """
        Run the main program
        """
        time_start = time.time()

        while True:
            success, frame = self.cam.read()
            # Stop the program if no data source is available
            if not success:
                sys.exit("Failure: Unable to capture video. Please verify your camera settings.")

            # Calculate the current FPS
            # This is an average measurement over 10 frames
            self.fps_counter += 1
            if self.fps_counter % self.settings.FPS_AVG_MEASURE_TIME == 0:
                time_end = time.time()
                self.fps = self.settings.FPS_AVG_MEASURE_TIME / (time_end - time_start)
                time_start = time.time()

            # Draw
            draw_label(frame, f"FPS: {self.fps}", x=10, y=10)

            result = self.model.process(frame)
            frame = self.drawer.draw(frame, result)
            draw_zones(frame)
            frame = self.detection.process_frame(frame, result)
            self.analyzer.send(self.detection.percentages)
            cv.imshow("Eye Cam", frame)

            # End the loop if the key 'Q' was pressed
            if cv.waitKey(1) == ord('q'):
                break

        # Stop the program
        self.cam.release()
        cv.destroyAllWindows()



# Entrypoint of the application.
while __name__ == "__main__":
    EyeCam().run()