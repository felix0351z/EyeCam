import time

import numpy as np

from detection.parcours import ParcoursDetection
from sensor.classes import SensorOutput
from yolo.classes import YOLOOutput


# A track keeps its frame counter, if it is missing for at most this time.
# If ByteTrack finds it again (same id), it counts as stable immediately.
TRACK_MEMORY_S = 0.5

# If the camera loses an object in a zone, its last danger value is kept for this time.
# Bridges single frames, in which YOLO misses the object because of motion blur.
CAMERA_HOLD_S = 0.4


class ParcoursStableDetection(ParcoursDetection):
    """
    Variant of ParcoursDetection, which is more robust against camera shake while walking.

    The up and down movement while walking causes blurred frames and jumping boxes.
    YOLO and ByteTrack then lose objects for single frames. Two additions bridge this:

    1. Track memory: The frame counter of a track is not deleted immediately when its id
       is missing, but only after TRACK_MEMORY_S. A track found again counts at once.

    2. Camera hold: If the camera danger of a zone suddenly drops to 0 (object lost),
       the last value is kept for CAMERA_HOLD_S. Only gaps are filled: as long as the
       camera sees something in the zone, its current value is used.

    The sensor and everything else are the same as ParcoursDetection.
    """

    def __init__(self):
        super().__init__()
        # track id -> (frame count, last seen)
        self._tracks: dict[int, tuple[int, float]] = {}

        self._camera_last = np.zeros(3)
        self._camera_last_seen = np.full(3, -np.inf)

    def _raw_danger(self, yolo_output: YOLOOutput | None, sensor_output: SensorOutput | None,
                    track_ids: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
        danger_yolo, danger_sensor = super()._raw_danger(yolo_output, sensor_output, track_ids)
        if yolo_output is None:
            return danger_yolo, danger_sensor

        now = time.monotonic()

        # Remember the last value of every zone, in which the camera sees something
        seen = danger_yolo > 0
        self._camera_last[seen] = danger_yolo[seen]
        self._camera_last_seen[seen] = now

        # Fill zones, which lost their object only a moment ago
        fill = ~seen & (now - self._camera_last_seen <= CAMERA_HOLD_S)
        return np.where(fill, self._camera_last, danger_yolo), danger_sensor

    def _stable_tracks(self, track_ids: np.ndarray | None, box_count: int) -> np.ndarray:
        """
        Like SensorFirstDetection._stable_tracks, but missing tracks keep their counter
        for TRACK_MEMORY_S.
        """
        if track_ids is None:
            return np.ones(box_count, dtype=bool)

        now = time.monotonic()
        for t in map(int, track_ids):
            count, _ = self._tracks.get(t, (0, now))
            self._tracks[t] = (count + 1, now)

        # Only forget tracks, which are missing for longer than TRACK_MEMORY_S
        self._tracks = {t: v for t, v in self._tracks.items() if now - v[1] <= TRACK_MEMORY_S}

        return np.array([self._tracks[int(t)][0] >= self.MIN_TRACK_FRAMES for t in track_ids], dtype=bool)
