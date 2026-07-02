import numpy as np
import cv2 as cv

from src import config


class YOLOv8Processor:
    MODEL_PATH: str = "../cnn/yolo8n.onnx"
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
        net_result = self._net_forward(frame)
        return self._map_result(net_result)


    def _net_forward(self, frame: np.ndarray) -> np.ndarray:
        # Create a blob from the frame
        # https://www.geeksforgeeks.org/python/how-opencvs-blobfromimage-works/
        blob = cv.dnn.blobFromImage(
            image=frame,
            scalefactor=1 / 255,    # Multiply the pixel values by a scale factor to normalize them
            size=(config.MODEL_INPUT_WIDTH, config.MODEL_INPUT_HEIGHT), # Scale to match the required size by the network
            mean=[0, 0, 0],         # Remove color bias by subtracting this color values.
            swapRB=True,            # Convert OpenCV’s BGR format to RGB
            crop=False
        )

        # Proceed with the model
        self.model.setInput(blob)
        result = self.model.forward(self.model.getUnconnectedOutLayers())
        return result


    def _map_result(self, result: np.ndarray) -> np.ndarray:
        class_ids = []
        confidences = []
        boxes = []

        # yolo_v8 has two twisted axes
        detections = np.transpose(result[0][0])

        # Go through every detection
        for detection in detections:
            confidence = float(np.max(detection[:4]))  # Coco class attributes
            class_id = np.argmax(detection[4:])

            # Check if the confidence of the recognized class is high enough
            if confidence > config.SCORE_THRESHOLD:
                # Add confidence, class id and box
                confidences.append(confidence)
                class_ids.append(class_id)
                boxes.append(detection[:4])

        return np.array([class_ids, confidences, boxes])