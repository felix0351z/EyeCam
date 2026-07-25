import abc
from dataclasses import dataclass

import numpy as np

from processing.letterbox import LetterboxTransform


@dataclass
class YOLOInput:
    input: np.ndarray | any
    transform: LetterboxTransform


@dataclass
class YOLOOutput:
    image: np.ndarray
    confidences: np.ndarray
    class_names: np.ndarray
    boxes: np.ndarray


class Framework(abc.ABC):

    @abc.abstractmethod
    def pre_process(self, image: np.ndarray) -> YOLOInput:
        pass

    @abc.abstractmethod
    def infer(self, data: YOLOInput) -> np.ndarray:
        pass


class YOLOProcessor(abc.ABC):

    @abc.abstractmethod
    def post_process(self, data: YOLOInput, net: np.ndarray) -> YOLOOutput:
        pass
