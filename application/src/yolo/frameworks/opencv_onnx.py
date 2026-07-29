import cv2 as cv
import numpy as np

from yolo.interfaces import Framework, YOLOInput
from yolo.utils.blob import create_blob
from yolo.utils.letterbox import letterbox


class OpenCVOnnxFramework(Framework):
    """
    Use the Deep-Neural-Network Module (dnn) from OpenCV.
    This supports the ONNX engine to run .onnx models.
    """

    def __init__(self, config: dict):
        # Load the model
        self.net: cv.dnn.Net = cv.dnn.readNet(config["model_path"])
        self.output_layer = self.net.getUnconnectedOutLayersNames()


    def pre_process(self, image: np.ndarray) -> YOLOInput:
        # Resize the image, create letterbox and transform it to a blob
        resized, transform = letterbox(image)
        blob = create_blob(resized)

        return YOLOInput(blob, transform)

    def infer(self, data: YOLOInput) -> np.ndarray:

        # Set data in input layer
        self.net.setInput(data.input)
        return self.net.forward(self.output_layer)[0]

