import sys
import time

import cv2 as cv

from src.config import FPS_AVG_MEASURE_TIME


class EyeCamCamera:

    def __init__(self):
        self.cam = cv.VideoCapture(0)
        self.fps_counter = 0

    def run(self):
        time_start = time.time()

        while True:
            success, frame = self.cam.read()
            # Stop the program if no data source is available
            if not success:
                sys.exit("Failure: Unable to capture video. Please verify your camera settings.")

            # Calculate the current FPS
            # This is an average measurement over 10 frames
            self.fps_counter += 1
            if self.fps_counter % FPS_AVG_MEASURE_TIME == 0:
                time_end = time.time()
                fps = FPS_AVG_MEASURE_TIME / (time_end - time_start)
                time_start = time.time()

            # End the loop if the key 'Q' was pressed
            if cv.waitKey(1) == ord('q'):
                break

        # Stop the program
        self.cam.release()
        cv.destroyAllWindows()



# Entrypoint of the application.
while __name__ == "__main__":
    EyeCamCamera()