import abc
import time
from collections.abc import Callable
from enum import Enum

from yolo.classes import YOLOOutput


class MoveDirection(Enum):
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

        self._last_move = time.monotonic()
        self._subscriber = []

    def add_subscriber(self, subscriber: Callable):
        """
        Add a subscriber to the detection algorithm.
        """

        self._subscriber.append(subscriber)


    @abc.abstractmethod
    def calculate(self, yolo_output: YOLOOutput):
        """
        Algorithm logic, implemented by all subclasses.
        Needs to be called every frame in the main loop
        """
        pass


    def _move(self, direction: MoveDirection):
        """
        Move if there is an obstacle in the way.
        This will notify all subscribers.
        """

        # Cooldown if the latest move happened was less than 2 seconds ago
        if (time.monotonic() - self._last_move) < 2:
            return

        self._last_move = time.monotonic()
        for caller in self._subscriber:
            caller(direction)
