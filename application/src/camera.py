import abc
import sys

import numpy as np


class CameraSource(abc.ABC):
    @abc.abstractmethod
    def read(self) -> np.ndarray:
        pass

    @abc.abstractmethod
    def release(self) -> None:
        pass


class OpenCvCameraSource(CameraSource):

    def __init__(self):
        import cv2 as cv
        self.cam = cv.VideoCapture(0)


    def read(self) -> np.ndarray:
        success, frame = self.cam.read()
        if not success:
            sys.exit("Failure: Unable to capture video. Please verify your camera settings.")
        return frame

    def release(self) -> None:
        self.cam.release()

class PicamCameraSource(CameraSource):

    def __init__(self):
        from picamera2 import Picamera2
        self.picam = Picamera2()
        config = self.picam.create_preview_configuration(
            main={"size": (640, 640), "format": "RGB888"}
        )
        self.picam.configure(config)
        self.picam.start()

    def read(self) -> np.ndarray:
        return self.picam.capture_array()

    def release(self) -> None:
        self.picam.stop()