import abc
from typing import Any

import numpy as np
import cv2 as cv

from src.settings import EyeCamSettings


class YOLOModel(abc.ABC):


    MODEL_SIZE = (640, 640)
    # Width and length of the video input
    # This is the default image size used by the YOLO models
    # https://docs.ultralytics.com/tasks/detect#train

    @property
    @abc.abstractmethod
    def model_path(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def nms(self) -> bool:
        pass

    @property
    @abc.abstractmethod
    def central_coordinates(self) -> bool:
        pass

    @abc.abstractmethod
    def map_result(self, result: np.ndarray) -> list[list[Any]]:
        pass

    def __init__(self, settings: EyeCamSettings):
        self.settings = settings

        # Load the onnx model
        # TODO: Change to a more performaent engine another time
        self.model: cv.dnn.Net = cv.dnn.readNet(self.model_path)

    def process(self, frame: np.ndarray) -> np.ndarray:
        # Create a blob from the frame
        # https://www.geeksforgeeks.org/python/how-opencvs-blobfromimage-works/
        blob = cv.dnn.blobFromImage(
            image=frame,
            scalefactor=1 / 255,    # Multiply the pixel values by a scale factor to normalize them
            size=self.MODEL_SIZE,   # Scale to match the required size by the network
            mean=[0, 0, 0],         # Remove color bias by subtracting this color values.
            swapRB=True,            # Convert OpenCV’s BGR format to RGB
            crop=False
        )

        # Proceed with the model
        self.model.setInput(blob)
        result = self.model.forward(self.model.getUnconnectedOutLayersNames())
        return self.map_result(result)


class YOLOv8Model(YOLOModel):

    @property
    def model_path(self) -> str:
        return self.settings.PROJECT_PATH + "/models/yolov8n.onnx"

    @property
    def central_coordinates(self) -> bool:
        return True

    @property
    def nms(self) -> bool:
        return True

    def map_result(self, result: np.ndarray) -> list[list[Any]]:
        class_ids = []
        confidences = []
        boxes = []

        # yolo_v8 has two twisted axes, therefore we need to transpose them
        detections = np.transpose(result[0][0])

        # Go through every detection
        for detection in detections:

            # [center x, center y, width, height, and 80 coco class scores]
            # Get the class with the highest confidence and check if it's high enough
            confidence = float(np.max(detection[4:]))
            class_id = np.argmax(detection[4:])

            # Check if the confidence of the recognized class is high enough
            if confidence > self.settings.SCORE_THRESHOLD:
                # Add confidence, class id and box
                confidences.append(confidence)
                class_ids.append(class_id)
                boxes.append(detection[:4])

        return [class_ids, confidences, boxes]

class YOLOv5Model(YOLOModel):

    @property
    def model_path(self) -> str:
        return self.settings.PROJECT_PATH + "/models/yolov5s.onnx"

    @property
    def central_coordinates(self) -> bool:
        return True

    @property
    def nms(self) -> bool:
        return True

    def map_result(self, result: np.ndarray) -> list[list[Any]]:
        class_ids = []
        confidences = []
        boxes = []

        detections = result[0][0]

        # Go through every detection
        for detection in detections:

            # [center x, center y, width, height, objectness and 80 coco class scores]
            # YoloV5 has an objectness score. This is like an average confidence for all classes
            objectness = detection[4]

            # Check if the objectness is high enough
            if objectness > self.settings.SCORE_THRESHOLD:
                # Proceed and check if the class score is also high enough
                classes_confidences = detection[5:]
                class_id = np.argmax(classes_confidences)

                if classes_confidences[class_id] > self.settings.SCORE_THRESHOLD:
                    # If both confidences are valid, add the detection
                    confidences.append(objectness)
                    class_ids.append(class_id)
                    boxes.append(detection[:4])

        return [class_ids, confidences, boxes]

class YOLOv26Model(YOLOModel):

    @property
    def model_path(self) -> str:
        return self.settings.PROJECT_PATH + "/models/yolo26n.onnx"

    @property
    def central_coordinates(self) -> bool:
        return False

    @property
    def nms(self) -> bool:
        return False

    def map_result(self, result: np.ndarray) -> list[list[Any]]:
        class_ids = []
        confidences = []
        boxes = []

        detections = result[0][0]

        # Go through every detection
        for detection in detections:

            # [x1, y1, x2, y2, confidence, class_id]
            # v26 uses 2 coordinates instead of the center coordinates like the older models.
            # In addition, the model automatically returns the class id with the highest confidence.
            confidence = detection[4]

            # Check if the confidence is high enough
            if confidence > self.settings.SCORE_THRESHOLD:
                confidences.append(confidence)
                class_ids.append(detection[5])
                boxes.append(detection[:4])

        return [class_ids, confidences, boxes]