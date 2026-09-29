from collections import deque

import numpy as np

from detection.classes import DetectionAlgorithm, DodgeDirection
from yolo.classes import YOLOOutput

class ZoneBasedDetection(DetectionAlgorithm):


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
        self._percentages = [deque([0.0] * 10, maxlen=10,)] * 3

    def get_percentages(self):
        windows = np.array(self._percentages)
        return np.mean(windows, axis=1)

    def calculate_zone_coverage(self, image_shape: np.ndarray, boxes: np.ndarray):
        # Calculate width and height
        # Because there are 3 zones, one zone has 1/3 width
        zone_height = image_shape[0]
        zone_width = image_shape[1] / 3

        # Calculate start and end width of each zone
        zones = np.array([[0, 1], [1, 2], [2, 3]]) * zone_width

        for (i, (x_start, x_end)) in enumerate(zones):

            # Boxes
            x1 = boxes[:, 0]; y1 = boxes[:, 1]
            x2 = boxes[:, 2]; y2 = boxes[:, 3]
            boxes_height = np.abs(y2 - y1)

            # If the box starts before the current zone, take the start width of the zone
            x1[x1 < x_start] = x_start
            # If the box ends after the current zone, take the end width of the zone
            x2[x2 > x_end] = x_end

            # Negative values mean, that the box is in another zone, so these should be ignored
            boxes_width = np.maximum(x2 - x1, 0)

            # Calculate the coverage of each box for the current zone
            percentage = (boxes_width * boxes_height) / (zone_width * zone_height)

            # Take the box with the largest coverage for the zone
            if len(percentage) > 0:
                self._percentages[i].append(np.max(percentage))


    def _calculate(self, yolo_output: YOLOOutput):
        # Cooldown
        if self._is_cooldown():
            return

        # Calculate the box coverage for each zone
        self.calculate_zone_coverage(yolo_output.image.shape, yolo_output.boxes)

        # 1. Check if an object coverages more than 50% in the zones
        percentages = self.get_percentages()
        available_zones = percentages < 0.5

        if not available_zones[1]:
            # If an obstacle is in the middle
            if available_zones[0]:
                # If the left zone has no obstacles
                self._dodge(DodgeDirection.LEFT)
            elif available_zones[2]:
                # If the right zone has no obstacles
                self._dodge(DodgeDirection.RIGHT)
            else:
                # Stop if there is no space left
                self._dodge(DodgeDirection.STOP)