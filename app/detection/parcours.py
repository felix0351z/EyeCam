from dataclasses import dataclass

import numpy as np

from detection.sensor_first import (
    SensorFirstDetection, camera_distances, sensor_cells, sensor_zone_masks,
    sensor_free_side, _danger, SENSOR_FAR_MM, SENSOR_NEAR_MM,
)
from sensor.classes import SensorOutput
from yolo.classes import YOLOOutput


# ---------------------------------
# Camera
# ---------------------------------

# Obstacles of the parcours, only COCO classes
PARCOURS_CLASSES = {
    0,   # person
    1,   # bicycle
    13,  # bench
    24,  # backpack
    28,  # suitcase
    56,  # chair
    57,  # couch
    58,  # potted plant
    59,  # bed
    60,  # dining table
}

# Same mapping as the sensor: the camera also triggers at ~1.3 m
CAM_FAR_MM = SENSOR_FAR_MM
CAM_NEAR_MM = SENSOR_NEAR_MM


# ---------------------------------
# Obstacle memory
# ---------------------------------

# Bottom rows of the sensor grid (row 0 = top, as shown in the Analyzer).
# Please check: hold a hand low in front of the sensor, it must appear in these rows.
SENSOR_BOTTOM_ROWS = (6, 7)

# An obstacle is only remembered if it was nearer than this when it disappeared
MEMORY_START_MAX_MM = 2500
# ... and the person was walking towards it
MEMORY_MIN_SPEED_MM_S = 200
# It counts as disappeared if the middle is free or suddenly much farther away
MEMORY_JUMP_MM = 300

# Approach speed while remembering, clipped to normal walking speeds
MEMORY_SPEED_MIN_MM_S = 400
MEMORY_SPEED_MAX_MM_S = 1500

# Must be shorter than the move cooldown (2 s), so the memory sends at most one signal
MEMORY_DURATION_S = 1.5

# Time window to measure the approach speed
SPEED_WINDOW_S = 0.5


@dataclass
class _MiddleSample:
    timestamp: float
    distance: float     # mm, np.inf if the middle is free
    bottom: bool        # nearest cell is in SENSOR_BOTTOM_ROWS
    speed: float        # mm/s, positive = getting nearer
    free_side: float


@dataclass
class _Memory:
    start: float
    distance: float
    speed: float
    free_side: float

    def distance_at(self, timestamp: float) -> float:
        return max(0.0, self.distance - self.speed * (timestamp - self.start))


class ParcoursDetection(SensorFirstDetection):
    """
    Variant of SensorFirstDetection for the parcours (chairs, tables in a corridor).

    The sensor cannot be tilted and does not see the floor. Objects lower than the
    device (table ~75 cm, chair ~90 cm) leave the sensor's field of view at the bottom
    while approaching (table at ~1.7 m, chair at ~1.2 m). Two additions handle this:

    1. Tilted camera (~30°): It sees the floor from ~1 m to ~7 m, so exactly the region
       below the sensor. Distances are estimated from the bottom edge of the boxes
       and use the same mapping as the sensor (triggers at ~1.3 m).

    2. Obstacle memory: If the nearest obstacle in the middle was in the bottom rows,
       the person was approaching and it suddenly disappears, it is kept as a virtual
       obstacle for MEMORY_DURATION_S. Its distance keeps decreasing with the last
       measured approach speed.

    Decision logic (corridor, hysteresis, direction) is the same as SensorFirstDetection.
    """

    MIN_TRACK_FRAMES = 2

    def __init__(self):
        super().__init__()
        self._samples: list[_MiddleSample] = []
        self._memory: _Memory | None = None

    def _raw_danger(self, yolo_output: YOLOOutput | None, sensor_output: SensorOutput | None,
                    track_ids: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:

        # 1. Camera
        if yolo_output is not None:
            stable = self._stable_tracks(track_ids, len(yolo_output.boxes))
            distances = camera_distances(yolo_output, stable, PARCOURS_CLASSES)
            danger_yolo = _danger(distances, CAM_FAR_MM, CAM_NEAR_MM)
        else:
            danger_yolo = np.zeros(3)

        # 2. Sensor with obstacle memory
        if sensor_output is None:
            self._samples.clear()
            self._memory = None
            self._free_side = 0.0
            return danger_yolo, np.zeros(3)

        distances = self._sensor_with_memory(sensor_output)
        return danger_yolo, _danger(distances, SENSOR_FAR_MM, SENSOR_NEAR_MM)

    def _sensor_with_memory(self, sensor_output: SensorOutput) -> np.ndarray:
        dist = sensor_cells(sensor_output)
        masks = sensor_zone_masks(dist)

        distances = np.full(3, np.inf)
        for i, mask in enumerate(masks):
            if np.any(mask):
                distances[i] = np.min(dist[mask])

        # Row of the nearest cell in the middle
        bottom = False
        if np.isfinite(distances[1]):
            middle = np.where(masks[1], dist, np.inf)
            row, _ = np.unravel_index(np.argmin(middle), middle.shape)
            bottom = row in SENSOR_BOTTOM_ROWS

        now = sensor_output.timestamp
        sample = _MiddleSample(now, float(distances[1]), bottom,
                               self._approach_speed(now, distances[1]),
                               sensor_free_side(sensor_output))

        # The same sensor frame can be read twice, if the main loop is faster than the sensor
        if self._samples and self._samples[-1].timestamp == now:
            return self._apply_memory(distances, now)

        # Start the memory, if an approaching obstacle left the field of view at the bottom
        if self._samples:
            last = self._samples[-1]
            disappeared = sample.distance > last.distance + MEMORY_JUMP_MM
            if (last.bottom and disappeared
                    and last.distance <= MEMORY_START_MAX_MM
                    and last.speed >= MEMORY_MIN_SPEED_MM_S):
                speed = float(np.clip(last.speed, MEMORY_SPEED_MIN_MM_S, MEMORY_SPEED_MAX_MM_S))
                self._memory = _Memory(last.timestamp, last.distance, speed, last.free_side)

        self._samples.append(sample)
        self._samples = [s for s in self._samples if now - s.timestamp <= SPEED_WINDOW_S]

        self._free_side = sample.free_side
        return self._apply_memory(distances, now)

    def _apply_memory(self, distances: np.ndarray, now: float) -> np.ndarray:
        if self._memory is None:
            return distances

        if now - self._memory.start > MEMORY_DURATION_S:
            self._memory = None
            return distances

        # The obstacle is not visible anymore: also use the direction from before
        distances[1] = min(distances[1], self._memory.distance_at(now))
        self._free_side = self._memory.free_side
        return distances

    def _approach_speed(self, now: float, distance: float) -> float:
        """
        Approach speed in mm/s from the oldest sample in the time window. 0 if unknown.
        """
        if not np.isfinite(distance):
            return 0.0

        for s in self._samples:
            dt = now - s.timestamp
            if np.isfinite(s.distance) and dt >= 0.2:
                return (s.distance - distance) / dt
        return 0.0
