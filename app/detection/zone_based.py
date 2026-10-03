from collections import deque
from dataclasses import dataclass

import numpy as np

from detection.classes import DetectionAlgorithm, MoveDirection
from detection.tracker.byte_tracker import BYTETracker
from yolo.classes import YOLOOutput

class Tracker:
    """
    ByteTrack Tracker
    """

    @dataclass
    class TrackerArgs:
        track_thresh: float = 0.5
        track_buffer: int = 30
        match_thresh: float = 0.8
        mot20: bool = False

    def __init__(self):
        self._tracker = BYTETracker(self.TrackerArgs())

    def update(self, yolo_output: YOLOOutput, image_shape):
        # Boxes is a 2D ndarray, containing [ [x1, y2, x2, y2] , ...]
        # Confidences is a 1D Array, containing the confidence value for all detections in the same order
        # Add the confidences as a column to the boxes. This is the correct input type for ByteTrack.
        out_results = np.column_stack((yolo_output.boxes, yolo_output.confidences)).astype(np.float32)
        if len(out_results) == 0:
            out_results = np.empty((0, 5))

        # The two parameters originally are for the size used by the network and the original image size.
        # Because rescaling already happened, just use the original image size twice.
        h, w = image_shape[:2]
        tracks = self._tracker.update(out_results, (h, w), (h, w))

        # Create a new output ndarray, containing [ [x1, y1, x2, y2, score, track_id], ...]
        if tracks:
            out = np.array([t.tlbr for t in tracks], dtype=np.float32)
        else:
            out = np.empty((0, 6), dtype=np.float32)
        # Update the boxes
        yolo_output.boxes = out





class ZoneBasedDetection(DetectionAlgorithm):
    MOVE_THRESHOLD = 0.5


    def __init__(self):
        """
        This class implements a dumb-simple zone-based detection algorithm.

        The picture will be separated into 3 parts: Left, Middle and a Right zone.
        If a box covers more than X % of the middle zone, decide to dodge to left or right.
        If the left or right zone is obstacle free (less than X %), move there.

        This class completely relies on the YOLO output.
        A distance measurement by a sensor would be preferred instead.
        """
        super().__init__()
        self._percentages = [deque([0.0] * 10, maxlen=10) for _ in range(3)]

    def get_percentages(self):
        windows = np.array(self._percentages)
        return np.mean(windows, axis=1)

    def calculate_zone_coverage(self, image_shape, boxes: np.ndarray):
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
            self._percentages[i].append(np.max(percentage) if len(percentage) > 0 else 0.0)


    def calculate(self, yolo_output: YOLOOutput):
        # Calculate the box coverage for each zone
        self.calculate_zone_coverage(yolo_output.image.shape, yolo_output.boxes)
        left, middle, right = self.get_percentages()

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

