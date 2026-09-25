import abc

import numpy as np


# TODO
class DetectionAlgorithm(abc.ABC):

    @abc.abstractmethod
    def process_frame(self, frame: np.ndarray, net_output: np.ndarray) -> np.ndarray:
        pass