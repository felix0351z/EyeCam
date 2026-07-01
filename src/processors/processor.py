import numpy as np
import cv2 as cv

from src import config


class YOLOProcessor:
    MODEL_PATH: str = "../cnn/yolo26n.onnx"
    COCO_PATH: str = "../cnn/coco.names"

    def __init__(self):
        self.classes = None
        self.model = None

    def initialize(self, model_path: str = MODEL_PATH):

        # Load the coco file
        with open(self.COCO_PATH, 'r') as file:
            self.classes = file.read().rstrip('\n').split('\n')

        # Load the onnx model
        # TODO: Change to a more performaent engine another time
        self.model: cv.dnn.Net = cv.dnn.readNet(model_path)

    def process(self, frame: np.ndarray) -> np.ndarray:

        # Create a blob from the frame
        # https://www.geeksforgeeks.org/python/how-opencvs-blobfromimage-works/
        blob = cv.dnn.blobFromImage(
            image=frame,
            scalefactor=1 / 255,    # Multiply the pixel values by a scale factor to normalize them
            size=(config.VIDEO_INPUT_WIDTH, config.VIDEO_INPUT_HEIGHT), # Scale to match the required size by the network
            mean=[0, 0, 0],         # Remove color bias by subtracting this color values.
            swapRB=True,            # Convert OpenCV’s BGR format to RGB
            crop=False
        )

        # Proceed with the model
        self.model.setInput(blob)
        result = self.model.forward(self.model.getUnconnectedOutLayers())

        return result