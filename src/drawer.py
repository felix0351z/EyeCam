import numpy as np
import cv2 as cv

from src import config


class Drawer:


    def __init__(self, camera_width: int = config.MODEL_INPUT_WIDTH, camera_height: int = config.MODEL_INPUT_HEIGHT):
        self.camera_width = camera_width
        self.camera_height = camera_height


    def draw_boxes(self, frame: np.ndarray, net_output: np.ndarray, nms: bool = True) -> np.ndarray:
        """
        Draw bounding boxes around the detected objects.
        :param frame: The input frame or image
        :param net_output: The output of the cnn model
        :param nms: Apply a Non-Maximum-Suppression. Needed in older cnn models
        :return The input frame with the drawn boxes on it
        """

        # Get the output data from the cnn model
        _, confidences, boxes = net_output

        # Draw the boxes with the right scaling of the input frame
        draw_boxes = []
        x_scale = self.camera_width / config.MODEL_INPUT_WIDTH
        y_scale =self.camera_height / config.MODEL_INPUT_HEIGHT

        # center x, center y, width, height
        x, y, w, h = boxes
        left = int((x - w/2) * x_scale)
        top = int((y - h/2) * y_scale)
        width = int(w * x_scale)
        height = int(h * y_scale)
        draw_boxes.append(np.array([left, top, width, height]))

        # Perform a Non-Maximum-Suppression
        if nms:
            nms_indices = cv.dnn.NMSBoxes(
                bboxes=draw_boxes,
                scores=confidences,
                score_threshold=config.SCORE_THRESHOLD,
                nms_threshold=config.NMS_THRESHOLD
            )
            boxes = nms_indices

        # Draw the boxes
        for box in boxes:
            left, top, width, height = box
            cv.rectangle(
                img=frame,
                pt1=(left, top),
                pt2=(left + width, top + height),
                color=config.COLOR_BLUE,
                thickness=3
            )

        return frame

    def draw_labels(self):
        pass




