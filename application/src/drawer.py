import numpy as np
import cv2 as cv

from yolo.interfaces import YOLOOutput

# BGR
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)

FONT_FACE = cv.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7



def draw(data: YOLOOutput):
    """
    Draw bounding boxes around the detected objects.
    """
    for i, box in enumerate(data.boxes):
        # Draw the boxes
        pt1, pt2 = box
        cv.rectangle(img=data.image, pt1=box[0], pt2=box[1], color=COLOR_BLUE, thickness=3)

        # Draw the label
        label = "{}: {:.2f}".format(int(data.class_ids[i]), data.confidences[i])
        draw_label(data.image, label, x=pt1[0], y=pt1[1])


def draw_zones(frame: np.ndarray):
    image_height, image_width = frame.shape[:2]

    zone_size_width = int(image_width / 3)
    zones = np.array([1, 2, 3]) * zone_size_width

    for x in zones:
        cv.line(
            img=frame,
            pt1=(x, 0),
            pt2=(x, image_height),
            color=COLOR_BLUE,
        )


def draw_label(frame: np.ndarray, label: str, x: int, y: int):
    """
    Draw a single label on the frame.
    """

    # Calculate the size for the label box
    # baseline: y-coordinate relative to the bottom's lowest text point
    # (width, height),
    (width, height), baseline = cv.getTextSize(
        text=label,
        fontFace=FONT_FACE,
        fontScale=FONT_SCALE,
        thickness=1
    )

    # Draw the label
    cv.putText(
        img=frame, text=label,
        org=(x, y + height),
        fontFace=FONT_FACE, fontScale=FONT_SCALE,
        color=COLOR_YELLOW,
        thickness=1, lineType=cv.LINE_AA
    )






