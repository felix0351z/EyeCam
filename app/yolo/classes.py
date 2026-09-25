from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True, slots=True)
class LetterboxTransform:
    scale: float
    pad_x: float
    pad_y: float

@dataclass
class YOLOInput:
    input: np.ndarray
    transform: LetterboxTransform

@dataclass
class YOLOOutput:
    image: np.ndarray
    confidences: np.ndarray
    class_ids: np.ndarray
    boxes: np.ndarray