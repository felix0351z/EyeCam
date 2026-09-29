import abc
import time
from enum import Enum
from collections.abc import Callable

import numpy as np

from yolo.classes import YOLOOutput


class DodgeDirection(Enum):
    LEFT = 0
    RIGHT = 1
    STOP = 2



class DetectionAlgorithm(abc.ABC):

    def __init__(self):
        """
        Abstract class for any detection algorithm.

        A detection algorithm is the core logic, which decides if
        there is an obstacle and the user needs to act.

        To notify the bracelets or any other system like the Analyzer,
        use a subscriber method and listen for dodge events.
        """

        self._last_dodge = time.monotonic()
        self._subscriber = []

    def add_subscriber(self, subscriber: Callable[DodgeDirection]):
        """
        Add a subscriber to the detection algorithm.
        """

        self._subscriber.append(subscriber)


    def check(self, yolo_output: YOLOOutput):
        """
        Algorithm check
        This method needs to be called during the main loop
        """

        # Cooldown if the latest dodge happened was less than 2 seconds ago
        if (time.monotonic() - self._last_dodge) < 2:
            return

        self._calculate(yolo_output)


    @abc.abstractmethod
    def _calculate(self, yolo_output: YOLOOutput) -> np.ndarray:
        """
        Internal algorithm logic, implemented by all subclasses.
        """
        pass

    def _is_cooldown(self) -> bool:
        """
        Cooldown
        If the last action happened less than 2 seconds ago, true
        """
        return (time.monotonic() - self._last_dodge) < 2

    def _dodge(self, direction: DodgeDirection):
        """
        Dodge if there is an obstacle in the way.
        This will notify all subscribers.
        """

        self._last_dodge = time.monotonic()
        for caller in self._subscriber:
            caller(direction)

        pass
