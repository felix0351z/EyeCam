import numpy as np
import cv2 as cv

from yolo.interfaces import LetterboxTransform, YOLOOutput


def letterbox(frame: np.ndarray, model_size: int = 640, color=(114, 114, 114)):
    """
    Letterbox is a resize of the image with the goal of preserving the original aspect ratio.

    frame: The image frame
    model_size: The input-size of the model
    color: The color of the canvas for the letterbox
    """

    height, width = frame.shape[:2]

    # Calculate the needed scale
    scale = min(model_size / height, model_size / width)
    new_height, new_width = int(height * scale), int(width * scale)

    # Create the canvas and resize the image
    resized_frame = cv.resize(frame, (new_width, new_height))
    canvas = np.full(shape=(model_size, model_size, 3), fill_value=color, dtype=np.uint8)

    # Fill the corners with the canvas
    top = (model_size - new_height) // 2
    left = (model_size - new_width ) // 2
    canvas[top:top + new_height, left:left + new_width] = resized_frame

    return canvas, LetterboxTransform(scale, left, top)

def resize_boxes_central_coordinates(boxes: np.ndarray, transform: LetterboxTransform) -> np.ndarray:
    x, y = boxes[:, 0], boxes[:, 1]
    w, h = boxes[:, 2], boxes[:, 3]

    left = ((x - w / 2) - transform.pad_x) / transform.scale
    top = ((y - h / 2) - transform.pad_y) / transform.scale
    width = w / transform.scale
    height = h / transform.scale

    return np.column_stack([left, top, width, height]).astype(int)


def nms(data: YOLOOutput, score_threshold: float, nms_threshold: float = 0.45):
    # Apply a NMS
    indices = cv.dnn.NMSBoxes(
        bboxes=data.boxes, scores=data.confidences,
        score_threshold=score_threshold, nms_threshold=nms_threshold
    )

    indices = np.array(indices)

    left = data.boxes[indices, 0]
    top = data.boxes[indices, 1]
    width = data.boxes[indices, 2]
    height = data.boxes[indices, 3]

    data.boxes = np.column_stack([left, top, left+width, top+height])
    data.confidences = data.confidences[indices]
    data.class_ids = data.class_ids[indices]