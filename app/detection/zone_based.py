from typing import Any
from collections import deque

import cv2
import numpy as np

from detection.classes import DetectionAlgorithm


# TODO
class ZoneBasedDetection(DetectionAlgorithm):

    def __init__(self, model_size: tuple[int, int]):
        self.model_size = model_size
        self.percentages = [deque(maxlen=10), deque(maxlen=10), deque(maxlen=10)]

    def get_percentages(self):
        return list(map(lambda d: np.average(d), self.percentages))


    def calculate_zone_coverage(self, frame: np.ndarray, boxes: list[Any], debug: bool = True) -> np.ndarray:
        """
        Calculate the coverage of the 3 zones (left, middle, right) in percent.
        :param frame: The input frame
        :param boxes: The boxes returned by the cnn model. The boxes have to be in the format [x1, y1, x2, y2]
        :param debug: If true, the coverage for the middle zone will be displayed
        :return:
        """

        # Calculate the zone coordinates
        zone_width = int(frame.shape[1] / 3)
        zone_height = frame.shape[0]
        zone_size = zone_width * zone_height
        zones = np.array([[0, 1], [1, 2], [2, 3]]) * zone_width

        # Calculate the coverage for every box in the 3 zones
        for (i, (x_start, x_end)) in enumerate(zones):
            per = []
            for box in boxes:
                x1, y1 = box[0]
                x2, y2 = box[1]
                height = y2 - y1

                # Calculate the width for the box in the zone
                if x2 > x_end:
                    x2 = x_end
                if x1 < x_start:
                    x1 = x_start

                # Negative values mean, that the box is in another zone, so these should be ignored
                width = max(x2 - x1, 0)

                percentage = (width * height) / zone_size
                per.append(percentage)

                # Debug preview for zone middle
                if debug:
                    # Show the coverage for the middle zone
                    if i == 1:
                        debug_pt1 = (x1, y1)
                        debug_pt2 = (x2, y2)
                        cv2.rectangle(img=frame, pt1=debug_pt1, pt2=debug_pt2, color=(0, 255, 0), thickness=1)

            # Take the biggest box as reference
            if len(per) > 0:
                self.percentages[i].append(np.max(per))
        return frame


    def process_frame(self, frame: np.ndarray, net_output: np.ndarray) -> np.ndarray:
        # Get the output data from the cnn model
        class_ids, confidences, boxes = net_output

        # Calculate the coverage of the 3 zones
        frame = self.calculate_zone_coverage(frame, boxes)

        return frame