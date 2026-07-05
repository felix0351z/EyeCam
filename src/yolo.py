import abc
from typing import Any

import numpy as np
import cv2 as cv

from src.settings import EyeCamSettings


class YOLOModel(abc.ABC):

    MODEL_SIZE = (640, 640)
    """
    This is the default image size used by the yolo models.
    https://docs.ultralytics.com/tasks/detect#train
    """

    @property
    @abc.abstractmethod
    def model_path(self) -> str:
        """
        Path to the .onnx file
        """

        pass

    @property
    @abc.abstractmethod
    def nms(self) -> bool:
        """
        Apply a Non-Maximum-Suppression in the post-process.
        This step is unnecessary if a model already has built-im NMS.
        """

        pass

    @property
    @abc.abstractmethod
    def central_coordinates(self) -> bool:
        """
        Is the output of the model in the format [center x, center y, width, height] or
        are 2 points given like [x1, y1, x2, y2]
        """

        pass

    @abc.abstractmethod
    def map_result(self, result: np.ndarray) -> list[list[Any]]:
        """
        Map the result of the yolo model to a list in the format [class_ids, confidences, boxes]
        Every detection is one sequence, so class_ids[i] and confidences[i] are related to each other.
        class_ids: list[int]
        confidences: list[float]
        boxes: list[[x, y, width, height] or [x1, x2, y1, y2]]

        :param result: The output-layer of the model
        :return: [class_ids, confidences, boxes]
        """

        pass

    def __init__(self, settings: EyeCamSettings):
        """
        Load the model and initialize the variables
        :param settings: The EyeCamSettings from settings.py
        """

        self.settings = settings

        # Load the onnx model
        # TODO: Change to a more performaent engine another time
        self.model: cv.dnn.Net = cv.dnn.readNet(self.model_path)

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Process the frame with the model
        :param frame: The image frame captured by opencv
        :return: The model result in the format [class_ids, confidences, boxes]
        """

        # Create a blob from the frame
        # https://www.geeksforgeeks.org/python/how-opencvs-blobfromimage-works/
        blob = cv.dnn.blobFromImage(
            image=frame,
            scalefactor=1 / 255,  # Multiply the pixel values by a scale factor to normalize them
            size=self.MODEL_SIZE,  # Scale to match the required size by the network
            mean=[0, 0, 0],  # Remove color bias by subtracting this color values.
            swapRB=True,  # Convert OpenCV’s BGR format to RGB
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
        """
        YOLOv26 returns two points. No central point with width and height.
        https://docs.ultralytics.com/guides/end2end-detection#how-end-to-end-detection-works
        """
        return False

    @property
    def nms(self) -> bool:
        """
        No need for NMS because YOLOv26 already has built-in.
        https://docs.ultralytics.com/guides/end2end-detection#how-end-to-end-detection-works
        """
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
