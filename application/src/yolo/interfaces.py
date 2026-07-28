import abc
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


class Framework(abc.ABC):

    def __init__(self, config: dict):
        pass

    @abc.abstractmethod
    def pre_process(self, image: np.ndarray) -> YOLOInput:
        pass

    @abc.abstractmethod
    def infer(self, data: YOLOInput) -> np.ndarray:
        pass


class YOLOProcessor(abc.ABC):
    SCORE_THRESHOLD: float = 0.5

    def __init__(self, config: dict):
        pass

    @abc.abstractmethod
    def post_process(self, image: np.ndarray, transform: LetterboxTransform, net: np.ndarray) -> YOLOOutput:
        pass