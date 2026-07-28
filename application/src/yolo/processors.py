import numpy as np

from yolo.interfaces import YOLOProcessor, YOLOOutput, LetterboxTransform
from yolo.utils.letterbox import resize_boxes_central_coordinates, nms, resize_boxes


class YOLOv26EndToEndProcessor(YOLOProcessor):

    def post_process(self, image: np.ndarray, transform: LetterboxTransform, net: np.ndarray) -> YOLOOutput:
        # [1, 300, 6]
        # [x1, y1, x2, y2, confidence, class_id]
        boxes = net[0, :, :4]
        confidences = net[0, :, 4]
        class_ids = net[0, :, 5]

        mask = confidences > self.SCORE_THRESHOLD
        boxes = boxes[mask, :]
        confidences = confidences[mask]
        class_ids = class_ids[mask]


        resized_boxes = resize_boxes(boxes, transform)
        return YOLOOutput(image, confidences, class_ids, resized_boxes)



class YOLOv8Processor(YOLOProcessor):

    def post_process(self, image: np.ndarray, transform: LetterboxTransform, net: np.ndarray) -> YOLOOutput:
        # [center x, center y, width, height, and 80 coco class scores]
        # YOLOv8 has twisted axes
        detections = np.transpose(net[0])

        # Get confidences and class ids from the detections
        scores = detections[:, 4:]
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)

        # Only take values over threshold
        mask = confidences > self.SCORE_THRESHOLD

        boxes = detections[mask, :4]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        # Resize the boxes and change format to [left, top, width, height]
        boxes = resize_boxes_central_coordinates(boxes, transform)
        output = YOLOOutput(image, confidences, class_ids, boxes)

        # Apply NMS
        nms(data=output, score_threshold=self.SCORE_THRESHOLD)
        return output


class YOLOv5Processor(YOLOProcessor):

    def post_process(self, image: np.ndarray, transform: LetterboxTransform, net: np.ndarray) -> YOLOOutput:
        # YOLOv5 model output has shape (1, n ,85)
        # [center x, center y, width, height, objectness and 80 coco class scores]

        scores = net[0, :, 5:]
        confidences = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)

        mask = confidences > self.SCORE_THRESHOLD

        boxes = net[0, mask, :4]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        # Resize the boxes and change format to [left, top, width, height]
        boxes = resize_boxes_central_coordinates(boxes, transform)
        output = YOLOOutput(image, confidences, class_ids, boxes)

        # Apply NMS
        nms(data=output, score_threshold=self.SCORE_THRESHOLD)
        return output

