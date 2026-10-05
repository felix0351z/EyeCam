import numpy as np

from detection.classes import DetectionAlgorithm, MoveDirection
from yolo.classes import YOLOOutput


class ZoneBasedDetection(DetectionAlgorithm):
    """
    This class implements a dumb-simple zone-based detection algorithm.

    The picture will be separated into 3 parts: Left, Middle and a Right zone.
    If a box covers more than X % of the middle zone, decide to dodge to left or right.
    If the left or right zone is obstacle free (less than X %), move there.

    This class completely relies on the YOLO output.
    A distance measurement by a sensor would be preferred instead.
    """

    MOVE_THRESHOLD = 0.5
    SMOOTHING_RISE = 0.6
    SMOOTHING_FALL = 0.2


    def __init__(self):
        super().__init__()

        self._coverage = np.zeros(3, dtype=np.float32)


    def calculate_zone_coverage(self, image_shape, boxes: np.ndarray) -> np.ndarray:
        percentages = np.zeros(3)
        # Calculate width and height
        # Because there are 3 zones, one zone has 1/3 width
        zone_height = image_shape[0]
        zone_width = image_shape[1] / 3

        # Calculate start and end width of each zone
        zones = np.array([[0, 1], [1, 2], [2, 3]]) * zone_width

        # Boxes
        y1 = np.clip(boxes[:, 1], 0, zone_height)
        y2 = np.clip(boxes[:, 3], 0, zone_height)
        boxes_height = np.abs(y2 - y1)

        for (i, (x_start, x_end)) in enumerate(zones):
            # Clip the boxes to the current zone
            x1 = np.clip(boxes[:, 0], x_start, x_end)
            x2 = np.clip(boxes[:, 2], x_start, x_end)

            # Boxes outside the zone have a width of 0
            boxes_width = x2 - x1

            # Calculate the coverage of each box for the current zone
            percentage = (boxes_width * boxes_height) / (zone_width * zone_height)

            # Take the box with the largest coverage for the zone
            # If there are no boxes, the zone is free
            percentages[i] = np.max(percentage) if len(percentage) > 0 else 0.0
        return percentages


    def calculate(self, yolo_output: YOLOOutput):
        # Calculate the box coverage for each zone
        current_coverage = self.calculate_zone_coverage(yolo_output.image.shape, yolo_output.boxes)

        # Use an exponential moving average to smooth the zone coverage
        alpha = np.where(current_coverage > self._coverage, self.SMOOTHING_RISE, self.SMOOTHING_FALL)
        self._coverage = alpha * current_coverage + (1 - alpha) * self._coverage
        left, middle, right = self._coverage

        # No obstacle ahead
        if middle <= self.MOVE_THRESHOLD:
            return

        # Stop if both sides are blocked
        if min(left, right) > self.MOVE_THRESHOLD:
            self._move(MoveDirection.STOP)
        # Move to the side with less coverage
        elif left <= right:
            self._move(MoveDirection.LEFT)
        else:
            self._move(MoveDirection.RIGHT)

