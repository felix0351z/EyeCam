from dataclasses import dataclass

import numpy as np

from bytetrack.byte_tracker import BYTETracker
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

    def update(self, yolo_output: YOLOOutput, image_shape) -> np.ndarray:
        # Boxes is a 2D ndarray, containing [ [x1, y2, x2, y2] , ...]
        # Confidences and class ids are 1D arrays in the same order as the boxes
        # Stack them to [ [x1, y1, x2, y2, score, class_id], ...]. This is the input type for ByteTrack.
        out_results = np.column_stack(
            (yolo_output.boxes, yolo_output.confidences, yolo_output.class_ids)
        ).astype(np.float32)
        if len(out_results) == 0:
            out_results = np.empty((0, 6), dtype=np.float32)

        # The two parameters originally are for the size used by the network and the original image size.
        # Because rescaling already happened, just use the original image size twice.
        h, w = image_shape[:2]
        tracks = self._tracker.update(out_results, (h, w), (h, w))

        # ByteTrack can add or drop boxes, so update all fields to keep them in the same order
        if tracks:
            yolo_output.boxes = np.array([t.tlbr for t in tracks], dtype=np.float32)
            yolo_output.confidences = np.array([t.score for t in tracks], dtype=np.float32)
            yolo_output.class_ids = np.array([t.cls for t in tracks], dtype=int)
            track_ids = np.array([t.track_id for t in tracks], dtype=int)
        else:
            yolo_output.boxes = np.empty((0, 4), dtype=np.float32)
            yolo_output.confidences = np.empty(0, dtype=np.float32)
            yolo_output.class_ids = np.empty(0, dtype=int)
            track_ids = np.empty(0, dtype=int)

        return track_ids
