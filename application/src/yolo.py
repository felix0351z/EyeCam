import abc
from typing import Any, Sequence

import numpy as np
import cv2 as cv

from letterbox import letterbox, LetterboxTransform
from settings import EyeCamSettings


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
        Path to the model file
        This can be in the format .onnx or any other runtime format
        """

        pass

    @abc.abstractmethod
    def map_result(self, frame: np.ndarray, result: np.ndarray, transform: LetterboxTransform) -> list[list[Any]]:
        """
        Map the result of the yolo model to a list in the format [class_ids, confidences, boxes]
        Every detection is one sequence, so class_ids[i] and confidences[i] are related to each other.
        class_ids: list[int]
        confidences: list[float]
        boxes: list[(x1, y2), (x2, y2)]

        :param frame: The image frame
        :param result: The output-layer of the model
        :param transform The letterbox transformation from the preprocessing
        :return: [class_ids, confidences, boxes]
        """

        pass

    def __init__(self, settings: EyeCamSettings):
        """
        Load the model and initialize the variables
        :param settings: The EyeCamSettings from settings.py
        """

        self.settings = settings
        # Check if openvino is available. If not, fallback to the default onnx runtime from opencv
        try:
            import openvino as ov
            core = ov.Core()
            model = core.read_model(self.model_path)
            self.use_ov = True
            self.ov_compiled_model = core.compile_model(model, device_name="AUTO")
            self.ov_out_layer = self.ov_compiled_model.output(0)
        except ImportError:
            self.use_ov = False
            self.onnx_model: cv.dnn.Net = cv.dnn.readNet(self.model_path)

    def process(self, frame: np.ndarray) -> list[Any]:
        """
        Process the frame with the model
        :param frame: The image frame captured by opencv
        :return: The model result in the format [class_ids, confidences, boxes]
        """
        resized, transform = letterbox(frame, model_size=self.MODEL_SIZE[0])
        # Create a blob from the frame
        # https://www.geeksforgeeks.org/python/how-opencvs-blobfromimage-works/
        blob = cv.dnn.blobFromImage(
            image=resized,
            scalefactor=1 / 255,  # Multiply the pixel values by a scale factor to normalize them
            size=self.MODEL_SIZE,  # Scale to match the required size by the network
            swapRB=True,  # Convert OpenCV’s BGR format to RGB
            crop=False
        )

        if self.use_ov:
            # OpenVino
            result = self.ov_compiled_model(inputs=[blob])[self.ov_out_layer]
        else:
            # Default onnx runtime
            self.onnx_model.setInput(blob)
            result = self.onnx_model.forward(self.onnx_model.getUnconnectedOutLayersNames())

        return self.map_result(frame, result, transform)


class YOLOv8Model(YOLOModel):

    @property
    def model_path(self) -> str:
        return self.settings.PROJECT_PATH + "/models/yolov8n_openvino_model/yolov8n.xml"

    def map_result(self, frame: np.ndarray, result: np.ndarray, transform) -> list[list[Any]]:
        class_ids = []
        confidences = []
        boxes = []

        # yolo_v8 has two twisted axes, therefore we need to transpose them
        detections = np.transpose(result[0])

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

        # Resize and apply NMS
        resized_boxes = self.resize(boxes, transform)
        indices, nms_boxes = self.nms(confidences, resized_boxes)
        nms_class_ids = [class_ids[i] for i in indices]
        nms_confidences = [confidences[i] for i in indices]

        return [nms_class_ids, nms_confidences, nms_boxes]


    def nms(self, confidences: list[float], boxes: list[list[Any]]) -> tuple[Sequence[int], list[Any]]:
        output_boxes = []

        # Apply a NMS
        indices = cv.dnn.NMSBoxes(
            bboxes=boxes, scores=confidences,
            score_threshold=self.settings.SCORE_THRESHOLD, nms_threshold=self.settings.NMS_THRESHOLD
        )

        # Take the boxes with the highest coverage
        for i in indices:
            box = boxes[i]
            left, top, width, height = box
            pt1 = (left, top)
            pt2 = (left + width, top + height)

            output_boxes.append([pt1, pt2])

        return indices, output_boxes


    def resize(self, boxes: list[list[Any]], transform: LetterboxTransform) -> list[list[Any]]:
        output_boxes = []

        for box in boxes:
            x, y, w, h = box
            left = int(((x - w / 2) - transform.pad_x) / transform.scale)
            top = int(((y - h / 2) - transform.pad_y) / transform.scale)
            width = int(w / transform.scale)
            height = int(h / transform.scale)
            output_boxes.append(np.array([left, top, width, height]))

        return output_boxes


class YOLOv5Model(YOLOv8Model):

    @property
    def model_path(self) -> str:
        return self.settings.PROJECT_PATH + "/models/yolov5s.onnx"

    def map_result(self, frame: np.ndarray, result: np.ndarray, transform) -> list[list[Any]]:
        class_ids = []
        confidences = []
        boxes = []

        detections = result[0]

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

        # Resize and apply NMS
        resized_boxes = self.resize(boxes, transform)
        indices, nms_boxes = self.nms(confidences, resized_boxes)
        nms_class_ids = [class_ids[i] for i in indices]
        nms_confidences = [confidences[i] for i in indices]

        return [nms_class_ids, nms_confidences, nms_boxes]


class YOLOv26Model(YOLOModel):

    @property
    def model_path(self) -> str:
        return self.settings.PROJECT_PATH + "/models/yolo26n_openvino_model/yolo26n.xml"

    def map_result(self, frame: np.ndarray, result: np.ndarray, transform: LetterboxTransform) -> list[Any]:
        class_ids = []
        confidences = []
        boxes = []

        detections = result[0]

        # Go through every detection
        for detection in detections:

            # [x1, y1, x2, y2, confidence, class_id]
            # v26 uses 2 coordinates instead of the center coordinates like the older models.
            # In addition, the model automatically returns the class id with the highest confidence.
            # https://docs.ultralytics.com/guides/end2end-detection#how-end-to-end-detection-works
            confidence = detection[4]

            # Check if the confidence is high enough
            if confidence > self.settings.SCORE_THRESHOLD:
                confidences.append(confidence)
                class_ids.append(detection[5])
                boxes.append(detection[:4])

        out_boxes = self.resize(boxes, transform)
        return [class_ids, confidences, out_boxes]

    def resize(self, boxes: list[Any], transform: LetterboxTransform) -> list[list[Any]]:
        """
        Resize the box coordinates to the image dimensions
        :param boxes: The raw boxes in the format x1, y1, x2, y2
        :param transform: The Letterbox information from the preprocessing
        :return: The resized boxes in the format (x1, y1), (x2, y2)
        """
        output_boxes = []

        # Resize the dimensions
        for box in boxes:
            x1, y1, x2, y2 = box
            x1 = int((x1 - transform.pad_x) * transform.scale)
            y1 = int((y1 - transform.pad_y) * transform.scale)
            x2 = int((x2 - transform.pad_x) * transform.scale)
            y2 = int((y2 - transform.pad_y) * transform.scale)
            # Add box with the 2 points
            output_boxes.append([(x1, y1), (x2, y2)])

        return output_boxes