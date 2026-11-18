import math

import numpy as np

from detection.classes import DangerValues, DetectionAlgorithm, MoveDirection
from sensor.classes import SensorOutput
from yolo.classes import YOLOOutput


# ---------------------------------
# Geometry of the device (chest mount)
# ---------------------------------

# Height of camera and sensor above the floor. Depends on the person wearing it,
# +-15 cm only changes the camera distance estimate by about +-10 %.
DEVICE_HEIGHT_MM = 1300

# Width of the walking corridor in front of the person (shoulders + safety margin).
# Only obstacles inside this corridor can trigger a warning.
CORRIDOR_HALF_WIDTH_MM = 400

# Obstacles left/right outside of this angle belong to the side zones.
# Equals the two outer sensor columns (2 * 45° / 8).
SIDE_ANGLE_DEG = 11.25


# ---------------------------------
# Camera (Camera Module 3, normal lens)
# ---------------------------------

# The sensor of the module is 16:9 with 66° x 41°.
# For a square output (e.g. 640x640 or 320x320) libcamera crops the center, so both FoVs are ~41°.
# The image size itself is read from every frame. Only change this for a non-square output
# (horizontal FoV: 4:3 ~52°, 16:9 ~66°).
CAM_FOV_DEG = 41.0

# Downward tilt of the mounted camera. 0 = looking straight ahead.
# Must match the real mounting, it is used by all algorithms (also parcours.py).
# Recommended ~30°: the camera then sees the floor from ~1 m to ~7 m and finds
# low obstacles (chairs, tables) below the sensor's field of view.
CAM_TILT_DEG = 30.0

# Only these COCO classes are obstacles
CAM_CLASSES = {
    0,   # person
    1,   # bicycle
    2,   # car
    3,   # motorcycle
    5,   # bus
    7,   # truck
    10,  # fire hydrant
    11,  # stop sign
    12,  # parking meter
    13,  # bench
    15,  # cat
    16,  # dog
    25,  # umbrella
    28,  # suitcase
    56,  # chair
    57,  # couch
    58,  # potted plant
    60,  # dining table
    61,  # toilet
}

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


# No confidence filter here: model.py already filters (> 0.2) and ByteTrack only starts
# new tracks above 0.6. Running tracks may continue with lower scores (e.g. partly hidden).
CAM_MIN_TRACK_FRAMES = 3

CAM_FAR_MM = 2000
CAM_NEAR_MM = 500


# ---------------------------------
# Sensor (VL53L5CX, 8x8, 45° x 45°)
# ---------------------------------

SENSOR_FOV_DEG = 45.0
SENSOR_VALID_STATUS = (5, 9)
SENSOR_MAX_RANGE_MM = 4000
SENSOR_MAX_SIGMA_MM = 50

# A cell only counts if a neighbour cell sees something at a similar distance
SENSOR_NEIGHBOUR_TOLERANCE_MM = 250

SENSOR_FAR_MM = 2500
SENSOR_NEAR_MM = 500


class SensorFirstDetection(DetectionAlgorithm):
    """
    Sensor first detection algorithm.

    The sensor is the main source for distances. For every zone, the distance of the
    nearest obstacle is measured and converted to a danger value:
    - Middle: everything inside the walking corridor (+-40 cm), independent of the angle
    - Left/Right: the two outer sensor columns, used to choose the direction

    The camera supports the sensor. The distance of every YOLO box is estimated from
    the point where the box touches the floor. This needs no sensor and also works for
    low obstacles below the sensor's field of view (if the camera is tilted).
    The camera uses a stricter distance mapping (triggers at ~1.1 m, sensor at ~1.3 m).

    A warning is sent if the middle zone is above TRIGGER for CONFIRM_FRAMES frames,
    and it stays active until the middle zone falls below RELEASE (hysteresis).
    """

    TRIGGER = 0.6
    RELEASE = 0.45
    CONFIRM_FRAMES = 2

    SMOOTHING_RISE = 0.7
    SMOOTHING_FALL = 0.3

    # If both sides are nearly equal, move away from the obstacle
    SIDE_TIE = 0.1

    # A YOLO track needs to exist for this many frames to be used
    MIN_TRACK_FRAMES = CAM_MIN_TRACK_FRAMES

    def __init__(self):
        super().__init__()
        self._yolo_danger = np.zeros(3, dtype=np.float32)
        self._sensor_danger = np.zeros(3, dtype=np.float32)

        self._track_frames: dict[int, int] = {}
        self._frames_over_trigger = 0
        self._blocked = False
        self._free_side = 0.0

    def calculate(self, yolo_output: YOLOOutput | None, sensor_output: SensorOutput | None,
                  track_ids: np.ndarray | None = None) -> DangerValues:

        # 1. Raw danger values for every source
        danger_yolo, danger_sensor = self._raw_danger(yolo_output, sensor_output, track_ids)

        # 2. Smoothing: rise fast, fall slow
        self._yolo_danger = _smooth(self._yolo_danger, danger_yolo, self.SMOOTHING_RISE, self.SMOOTHING_FALL)
        self._sensor_danger = _smooth(self._sensor_danger, danger_sensor, self.SMOOTHING_RISE, self.SMOOTHING_FALL)
        result = DangerValues(yolo=self._yolo_danger, sensor=self._sensor_danger)

        # 3. Fusion and decision
        left, middle, right = np.maximum(self._yolo_danger, self._sensor_danger)

        if middle >= self.TRIGGER:
            self._frames_over_trigger += 1
        else:
            self._frames_over_trigger = 0

        if self._frames_over_trigger >= self.CONFIRM_FRAMES:
            self._blocked = True
        elif middle < self.RELEASE:
            self._blocked = False

        if not self._blocked:
            return result

        # Stop if both sides are blocked, otherwise move to the side with less danger
        if min(left, right) >= self.TRIGGER:
            self._move(MoveDirection.STOP)
        elif abs(left - right) < self.SIDE_TIE and self._free_side != 0:
            self._move(MoveDirection.RIGHT if self._free_side > 0 else MoveDirection.LEFT)
        elif left <= right:
            self._move(MoveDirection.LEFT)
        else:
            self._move(MoveDirection.RIGHT)

        return result

    def _raw_danger(self, yolo_output: YOLOOutput | None, sensor_output: SensorOutput | None,
                    track_ids: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
        """
        Unsmoothed danger values [left, middle, right] of camera and sensor.
        Also updates self._free_side for the direction decision.
        Subclasses can override this to change how the danger is measured.
        """
        if yolo_output is not None:
            stable = self._stable_tracks(track_ids, len(yolo_output.boxes))
            danger_yolo = camera_danger(yolo_output, stable)
        else:
            danger_yolo = np.zeros(3)

        if sensor_output is not None:
            danger_sensor = sensor_danger(sensor_output)
            self._free_side = sensor_free_side(sensor_output)
        else:
            danger_sensor = np.zeros(3)
            self._free_side = 0.0

        return danger_yolo, danger_sensor

    def _stable_tracks(self, track_ids: np.ndarray | None, box_count: int) -> np.ndarray:
        """
        Returns a mask of all boxes, whose track exists for at least MIN_TRACK_FRAMES frames.
        Without track ids, every box is stable.
        """
        if track_ids is None:
            return np.ones(box_count, dtype=bool)

        # Only keep the counters of the current tracks
        self._track_frames = {int(t): self._track_frames.get(int(t), 0) + 1 for t in track_ids}
        return np.array([self._track_frames[int(t)] >= self.MIN_TRACK_FRAMES for t in track_ids], dtype=bool)


def _smooth(previous: np.ndarray, current: np.ndarray, rise: float, fall: float) -> np.ndarray:
    alpha = np.where(current > previous, rise, fall)
    return (alpha * current + (1 - alpha) * previous).astype(np.float32)


def _danger(distance_mm: np.ndarray, far_mm: float, near_mm: float) -> np.ndarray:
    return np.clip((far_mm - distance_mm) / (far_mm - near_mm), 0, 1)


# ---------------------------------
# Sensor
# ---------------------------------

# Horizontal angle of the center of every sensor column, column 0 = left
_SENSOR_COLUMN_ANGLES = np.radians((np.arange(8) + 0.5 - 4) * SENSOR_FOV_DEG / 8)
_SENSOR_LEFT = np.degrees(_SENSOR_COLUMN_ANGLES) < -SIDE_ANGLE_DEG
_SENSOR_RIGHT = np.degrees(_SENSOR_COLUMN_ANGLES) > SIDE_ANGLE_DEG


def sensor_cells(sensor_output: SensorOutput) -> np.ndarray:
    """
    Filtered 8x8 distances in mm. Invalid cells and single outliers are np.nan.
    """
    dist = sensor_output.dist.astype(np.float32)
    valid = (
        np.isin(sensor_output.status, SENSOR_VALID_STATUS)
        & (sensor_output.sigma <= SENSOR_MAX_SIGMA_MM)
        & (dist > 0)
        & (dist <= SENSOR_MAX_RANGE_MM)
    )
    dist[~valid] = np.nan

    # 1. Remove single outliers: a cell needs a valid neighbour with a similar distance
    padded = np.pad(dist, 1, constant_values=np.nan)
    supported = np.zeros_like(valid)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            neighbour = padded[1 + dy:9 + dy, 1 + dx:9 + dx]
            with np.errstate(invalid="ignore"):
                supported |= np.abs(neighbour - dist) <= SENSOR_NEIGHBOUR_TOLERANCE_MM
    dist[~supported] = np.nan
    return dist


def sensor_zone_masks(dist: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    8x8 masks of the valid cells for [left, middle, right].
    Middle: lateral offset to the center line <= CORRIDOR_HALF_WIDTH_MM.
    """
    valid = ~np.isnan(dist)
    lateral = np.abs(dist * np.tan(_SENSOR_COLUMN_ANGLES))

    with np.errstate(invalid="ignore"):
        return (
            _SENSOR_LEFT & valid,
            (lateral <= CORRIDOR_HALF_WIDTH_MM) & valid,
            _SENSOR_RIGHT & valid,
        )


def sensor_distances(sensor_output: SensorOutput) -> np.ndarray:
    """
    Distance of the nearest obstacle in mm for [left, middle, right].
    np.inf, if the zone is free.
    """
    dist = sensor_cells(sensor_output)

    result = np.full(3, np.inf)
    for i, mask in enumerate(sensor_zone_masks(dist)):
        if np.any(mask):
            result[i] = np.min(dist[mask])
    return result


def sensor_free_side(sensor_output: SensorOutput) -> float:
    """
    Compares the mean distance of the left and right sensor half.
    Positive: the right side is more free, negative: the left side, 0: unknown.
    Invalid cells (nothing in range) count as SENSOR_MAX_RANGE_MM.
    """
    dist = np.where(np.isin(sensor_output.status, SENSOR_VALID_STATUS),
                    np.clip(sensor_output.dist, 0, SENSOR_MAX_RANGE_MM),
                    SENSOR_MAX_RANGE_MM).astype(np.float32)
    return float(np.mean(dist[:, 4:]) - np.mean(dist[:, :4]))


def sensor_danger(sensor_output: SensorOutput) -> np.ndarray:
    return _danger(sensor_distances(sensor_output), SENSOR_FAR_MM, SENSOR_NEAR_MM)


# ---------------------------------
# Camera
# ---------------------------------

def _floor_point(u: np.ndarray, v: np.ndarray, image_shape, tilt_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Projects image points onto the floor.
    Returns the forward distance and the lateral offset (left negative) in mm.
    Points above the horizon return np.inf.
    """
    height, width = image_shape[:2]
    f = (width / 2) / math.tan(math.radians(CAM_FOV_DEG / 2))
    tilt = math.radians(tilt_deg)

    # Ray in camera coordinates (x right, y down, z forward) rotated by the tilt
    x = (u - width / 2) / f
    y = (v - height / 2) / f
    down = y * math.cos(tilt) + math.sin(tilt)
    forward = math.cos(tilt) - y * math.sin(tilt)

    with np.errstate(divide="ignore", invalid="ignore"):
        scale = np.where(down > 1e-6, DEVICE_HEIGHT_MM / down, np.inf)
        return scale * forward, np.where(np.isfinite(scale), scale * x, 0.0)


def camera_distances(yolo_output: YOLOOutput, stable: np.ndarray, classes=None) -> np.ndarray:
    """
    Distance of the nearest obstacle in mm for [left, middle, right].
    The distance of a box is estimated from its bottom edge on the floor.
    If the bottom is cut off by the image, the object is at least as near
    as the floor at the bottom of the image.
    """
    result = np.full(3, np.inf)
    boxes = yolo_output.boxes
    if len(boxes) == 0:
        return result

    height, width = yolo_output.image.shape[:2]
    f = (width / 2) / math.tan(math.radians(CAM_FOV_DEG / 2))
    side_px = f * math.tan(math.radians(SIDE_ANGLE_DEG))

    classes = PARCOURS_CLASSES if classes is None else classes
    relevant = np.isin(yolo_output.class_ids, list(classes)) & stable

    for (x1, y1, x2, y2) in boxes[relevant]:
        bottom = min(y2, height - 1)
        distance, lateral = _floor_point(np.array([x1, x2]), np.array([bottom, bottom]),
                                         yolo_output.image.shape, CAM_TILT_DEG)
        distance = distance[0]
        if not np.isfinite(distance):
            continue

        # Left zone
        if x1 < width / 2 - side_px:
            result[0] = min(result[0], distance)
        # Middle zone: box overlaps the walking corridor
        if lateral[0] <= CORRIDOR_HALF_WIDTH_MM and lateral[1] >= -CORRIDOR_HALF_WIDTH_MM:
            result[1] = min(result[1], distance)
        # Right zone
        if x2 > width / 2 + side_px:
            result[2] = min(result[2], distance)

    return result


def camera_danger(yolo_output: YOLOOutput, stable: np.ndarray) -> np.ndarray:
    return _danger(camera_distances(yolo_output, stable), CAM_FAR_MM, CAM_NEAR_MM)
