import numpy as np
import cv2 as cv

from settings import EyeCamSettings

# BGR
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)

FONT_FACE = cv.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7

class Drawer:


    def __init__(self, settings: EyeCamSettings):
        """
        Initialize the drawer
        :param settings: The EyeCamSettings defined in settings.py
        :param model_size: The image size used by the cnn model
        """

        self.settings = settings

        # Load the coco file
        with open(self.settings.COCO_FILE_PATH, 'r') as file:
            self.coco_classes = file.read().rstrip('\n').split('\n')

    def draw(self, frame: np.ndarray, net_output: np.ndarray) -> np.ndarray:
        """
        Draw bounding boxes around the detected objects.
        :param frame: The input frame
        :param net_output: The result of the cnn model
        :return The input frame with the drawn boxes on it
        """

        # Get the output data from the cnn model
        class_ids, confidences, boxes = net_output

        for i, box in enumerate(boxes):
            # Draw the boxes
            pt1, pt2 = box
            cv.rectangle(img=frame, pt1=pt1, pt2=pt2, color=COLOR_BLUE, thickness=3)

            # Draw the label
            label = "{}: {:.2f}".format(self.coco_classes[int(class_ids[i])], confidences[i])
            draw_label(frame, label, x=pt1[0], y=pt1[1])

        return frame

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






