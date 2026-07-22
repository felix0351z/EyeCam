from dataclasses import dataclass

import cv2
import numpy as np

@dataclass(frozen=True, slots=True)
class LetterboxTransform:
    scale: float
    pad_x: float
    pad_y: float


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
    resized_frame = cv2.resize(frame, (new_width, new_height))
    canvas = np.full(shape=(model_size, model_size, 3), fill_value=color, dtype=np.uint8)

    # Fill the corners with the canvas
    top = (model_size - new_height) // 2
    left = (model_size - new_width ) // 2
    canvas[top:top + new_height, left:left + new_width] = resized_frame

    return canvas, LetterboxTransform(scale, left, top)