import numpy as np
import cv2 as cv

from src.settings import EyeCamSettings

# BGR
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)

FONT_FACE = cv.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7

class Drawer:


    def __init__(self, settings: EyeCamSettings, model_size: tuple[int, int]):
        """
        Initialize the drawer
        :param settings: The EyeCamSettings defined in settings.py
        :param model_size: The image size used by the cnn model
        """

        self.settings = settings
        self.model_size = model_size

        # Load the coco file
        with open(self.settings.COCO_FILE_PATH, 'r') as file:
            self.coco_classes = file.read().rstrip('\n').split('\n')

    def resize_boxes(self, image_shape: tuple[int], boxes: np.ndarray, central_coordinates: bool) -> list[np.ndarray]:
        """
        Resize the boxed to the width and height of the actual image.
        This is necessary because the cnn model uses a fixed image size.
        The input frame has a different size, the model will resize it.
        Therefore, the returned box-coordinates also need to be resized.

        :param image_shape: The acutal size of the captured frame
        :param boxes: The boxes returned by the cnn model
        :param central_coordinates: Is the model using a central coordinate with width and height or two coordinates
        :return: The resized boxes
        """


        output_boxes = []

        image_height, image_width = image_shape[:2]
        x_scale = image_width / self.model_size[0]
        y_scale = image_height / self.model_size[1]

        # center x, center y, width, height
        for box in boxes:
            if central_coordinates:
                x, y, w, h = box
                left = int((x - w/2) * x_scale)
                top = int((y - h/2) * y_scale)
                width = int(w * x_scale)
                height = int(h * y_scale)
                output_boxes.append(np.array([left, top, width, height]))
            else:
                x1, y1, x2, y2 = box
                x1 = int(x1 * x_scale)
                y1 = int(y1 * y_scale)
                x2 = int(x2 * x_scale)
                y2 = int(y2 * y_scale)
                output_boxes.append(np.array([x1, y1, x2, y2]))

        return output_boxes




    def draw(self, frame: np.ndarray, net_output: np.ndarray, nms: bool = True, central_coordinates: bool = True) -> np.ndarray:
        """
        Draw bounding boxes around the detected objects.
        :param frame: The input frame
        :param net_output: The result of the cnn model
        :param nms: Apply a Non-Maximum-Suppression
        :param central_coordinates: Is the model using a central coordinate with width and height or two coordinates
        :return The input frame with the drawn boxes on it
        """

        # Get the output data from the cnn model
        class_ids, confidences, boxes = net_output

        # Scale the boxes to the actual frame size
        scaled_boxes = self.resize_boxes(frame.shape, boxes, central_coordinates)

        # Perform a Non-Maximum-Suppression
        indices = range(len(scaled_boxes))
        if nms:
            indices = cv.dnn.NMSBoxes(
                bboxes=scaled_boxes,
                scores=confidences,
                score_threshold=self.settings.SCORE_THRESHOLD,
                nms_threshold=self.settings.NMS_THRESHOLD
            )

        for i in indices:
            box = scaled_boxes[i]

            if central_coordinates:
                left, top, width, height = box
                pt1 = (left, top)
                pt2 = (left + width, top + height)
            else:
                x1, y1, x2, y2 = box
                pt1 = (x1, y1)
                pt2 = (x2, y2)

            # Draw the boxes
            cv.rectangle(img=frame, pt1=pt1, pt2=pt2, color=COLOR_BLUE, thickness=3)

            # Draw the label
            label = "{}: {:.2f}".format(self.coco_classes[int(class_ids[i])], confidences[i])
            draw_label(frame, label, x=pt1[0], y=pt1[1])

        return frame




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






