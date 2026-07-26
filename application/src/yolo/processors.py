import numpy as np

from yolo.interfaces import YOLOProcessor, YOLOOutput, LetterboxTransform
from yolo.utils.letterbox import resize_boxes_central_coordinates, nms, resize_boxes


class YOLOv26EndToEndProcessor(YOLOProcessor):

    def post_process(self, image: np.ndarray, transform: LetterboxTransform, net: np.ndarray) -> YOLOOutput:
        class_ids = []
        confidences = []
        boxes = []

        # Go through every detection
        for detection in net[0]:
            # [x1, y1, x2, y2, confidence, class_id]
            confidence = detection[4]

            # Check if the confidence is high enough
            if confidence > self.SCORE_THRESHOLD:
                confidences.append(confidence)
                class_ids.append(detection[5])
                boxes.append(detection[:4])

        resized_boxes = resize_boxes(boxes, transform)
        return YOLOOutput(image, confidences, class_ids, resized_boxes)



class YOLOv8Processor(YOLOProcessor):

    def post_process(self, image: np.ndarray, transform: LetterboxTransform, net: np.ndarray) -> YOLOOutput:
        class_ids = []
        confidences = []
        boxes = []

        # YOLOv8 has twisted axes, therefore we need to transpose them
        detections = np.transpose(net[0])
        for detection in detections:
            # [center x, center y, width, height, and 80 coco class scores]
            # Get the class with the highest confidence and check if it's high enough
            confidence = float(np.max(detection[4:]))
            class_id = np.argmax(detection[4:])

            # Check if the confidence of the recognized class is high enough
            if confidence > self.SCORE_THRESHOLD:
                # Add confidence, class id and box
                confidences.append(confidence)
                class_ids.append(class_id)
                boxes.append(detection[:4])

        # Resize the boxes and change format to [left, top, width, height]
        boxes = resize_boxes_central_coordinates(boxes, transform)
        output = YOLOOutput(image, confidences, class_ids, boxes)

        # Apply NMS
        nms(data=output, score_threshold=self.SCORE_THRESHOLD)
        return output


class YOLOv5Processor(YOLOProcessor):

    def post_process(self, image: np.ndarray, transform: LetterboxTransform, net: np.ndarray) -> YOLOOutput:
        class_ids = []
        confidences = []
        boxes = []

        # YOLOv5 model output has shape (1, n ,85)
        for detection in net[0]:
            # [center x, center y, width, height, objectness and 80 coco class scores]
            # YOLOv5 has an objectness score. This is like an average confidence for all classes
            objectness = detection[4]

            # Check if the objectness is high enough
            if objectness > self.SCORE_THRESHOLD:
                # Proceed and check if the class score is also high enough
                classes_confidences = detection[5:]
                class_id = np.argmax(classes_confidences)

                if classes_confidences[class_id] > self.SCORE_THRESHOLD:
                    # If both confidences are valid, add the detection
                    confidences.append(objectness)
                    class_ids.append(class_id)
                    boxes.append(detection[:4])

        # Resize the boxes and change format to [left, top, width, height]
        boxes = resize_boxes_central_coordinates(boxes, transform)
        output = YOLOOutput(image, confidences, class_ids, boxes)

        # Apply NMS
        nms(data=output, score_threshold=self.SCORE_THRESHOLD)
        return output

