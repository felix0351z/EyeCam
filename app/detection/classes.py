import abc
import time
from collections.abc import Callable
from enum import Enum

from sensor.classes import SensorFrame
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
    def calculate(self, yolo_output: YOLOOutput, sensor: SensorFrame | None = None):
        """
        Algorithm logic, implemented by all subclasses.
        Needs to be called every frame in the main loop.

        sensor is None if there is no (or only outdated) sensor data.
        """
        pass

    def _decide(self, left: float, middle: float, right: float, threshold: float):
        """
        Shared decision logic for all zone based algorithms.
        Inputs are the (smoothed) obstacle values of the three zones.
        """

        # No obstacle ahead
        if middle <= threshold:
            return

        # Stop if both sides are blocked
        if min(left, right) > threshold:
            self._move(MoveDirection.STOP)
        # Move to the side with less coverage
        elif left <= right:
            self._move(MoveDirection.LEFT)
        else:
            self._move(MoveDirection.RIGHT)

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
