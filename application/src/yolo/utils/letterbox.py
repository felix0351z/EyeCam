import cv2 as cv
import numpy as np

from yolo.interfaces import YOLOOutput, LetterboxTransform


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

def resize_boxes_central_coordinates(boxes: list[np.ndarray], transform: LetterboxTransform) -> list[np.ndarray]:
    output = []
    for box in boxes:
        x, y, w, h = box
        left = int(((x - w / 2) - transform.pad_x) / transform.scale)
        top = int(((y - h / 2) - transform.pad_y) / transform.scale)
        width = int(w / transform.scale)
        height = int(h / transform.scale)
        output.append(np.array([left, top, width, height]))

    return output

def resize_boxes(boxes: list[np.ndarray], transform: LetterboxTransform)-> list[np.ndarray]:
    output = []
    for box in boxes:
        x1, y1, x2, y2 = box
        x1 = int((x1 - transform.pad_x) / transform.scale)
        y1 = int((y1 - transform.pad_y) / transform.scale)
        x2 = int((x2 - transform.pad_x) / transform.scale)
        y2 = int((y2 - transform.pad_y) / transform.scale)
        output.append(np.array([[x1, y1], [x2, y2]]))
        #output.append([(x1, y1), (x2, y2)])

    return output


def nms(data: YOLOOutput, score_threshold: float, nms_threshold: float = 0.45):
    output_boxes = []

    # Apply a NMS
    indices = cv.dnn.NMSBoxes(
        bboxes=data.boxes, scores=data.confidences,
        score_threshold=score_threshold, nms_threshold=nms_threshold
    )

    for i in indices:
        box = data.boxes[i]
        left, top, width, height = box
        output_boxes.append(np.array([[left, top], [left+width, top+height]]))
        #pt1 = (left, top)
        #pt2 = (left + width, top + height)
        #output_boxes.append([pt1, pt2])

    data.boxes = output_boxes
    data.confidences = [data.confidences[i] for i in indices]
    data.class_ids = [data.class_ids[i] for i in indices]