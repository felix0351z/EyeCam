import numpy as np

from detection.classes import DetectionAlgorithm, MoveDirection
from sensor.classes import SensorOutput
from yolo.classes import YOLOOutput

class ZoneDetection(DetectionAlgorithm):
    """
    This class implements a simple zone-based detection algorithm.

    YOLO:
    The picture will be separated into 3 parts: Left, Middle and a Right zone.
    The coverage in percent of the zones are the danger value (0-1)

    Sensor:
    The sensor values (8x8 grid) will also be separated into the same parts.
    For every zone, a danger value between 0 and 1 will be calculated.

    This algorithm calculates the danger value for YOLO and the sensor
    The highest danger value of both will be used.
    """
    MOVE_THRESHOLD = 0.5
    SMOOTHING_RISE = 0.6
    SMOOTHING_FALL = 0.2

    def __init__(self):
        super().__init__()
        self._yolo_danger = np.zeros(3, dtype=np.float32)
        self._sensor_danger = np.zeros(3, dtype=np.float32)


    def calculate(self, yolo_output: YOLOOutput | None, sensor_output: SensorOutput | None):

        danger_values_yolo = yolo_obstacle_map(yolo_output.image.shape, yolo_output.boxes) if yolo_output is not None else np.zeros(3)
        danger_values_sensor = sensor_obstacle_map(sensor_output) if sensor_output is not None else np.zeros(3)

        alpha_yolo = np.where(danger_values_yolo > self._yolo_danger, self.SMOOTHING_RISE, self.SMOOTHING_FALL)
        alpha_sensor = np.where(danger_values_sensor > self._sensor_danger, self.SMOOTHING_RISE, self.SMOOTHING_FALL)

        self._yolo_danger = alpha_yolo * danger_values_yolo + (1 - alpha_yolo) * self._yolo_danger
        self._sensor_danger = alpha_sensor * danger_values_sensor + (1 - alpha_sensor) * self._sensor_danger

        danger_values = np.maximum(self._yolo_danger, self._sensor_danger)
        left, middle, right = danger_values

        # No obstacle ahead
        if middle <= self.MOVE_THRESHOLD:
            return

        # Stop if both sides are blocked
        if min(left, right) > self.MOVE_THRESHOLD:
            self._move(MoveDirection.STOP)
        # Move to the side with less danger
        elif left <= right:
            self._move(MoveDirection.LEFT)
        else:
            self._move(MoveDirection.RIGHT)


def yolo_obstacle_map(image_shape, boxes: np.ndarray):
    coverage = np.zeros(3)

    # 1. Calculate width and height
    # Because there are 3 zones, one zone has 1/3 width
    zone_height = image_shape[0]
    zone_width = image_shape[1] / 3

    # 2. Calculate start and end width of each zone
    zones = np.array([[0, 1], [1, 2], [2, 3]]) * zone_width

    # 3. Boxes
    y1 = np.clip(boxes[:, 1], 0, zone_height)
    y2 = np.clip(boxes[:, 3], 0, zone_height)
    boxes_height = np.abs(y2 - y1)

    # 4. Zone coverage
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
        coverage[i] = np.max(percentage) if len(percentage) > 0 else 0.0

    return coverage


SENSOR_VALID_STATUS = (5, 9)
SENSOR_MAX_RANGE_MM = 4000 # mm, 4m
SENSOR_MAX_SIGMA_MM = 50 # mm

SENSOR_FAR_MM = 2500
SENSOR_NEAR_MM = 500

SENSOR_ZONES = ((0, 2), (2, 6), (6, 8))


def sensor_obstacle_map(sensor_output: SensorOutput):
    data = sensor_output.dist.astype(np.float32)

    # 1. Use a mask to set all invalid values to NaN
    valid_mask = (
        np.isin(sensor_output.status, SENSOR_VALID_STATUS) # Filter correct status
        & (sensor_output.sigma <= SENSOR_MAX_SIGMA_MM) # Filter sigma
        & (data <= SENSOR_MAX_RANGE_MM) # Filter range max
    )
    data[~valid_mask] = np.nan

    # 2. Filter out the last 2 rows for the floor
    # data = data[:-2]

    # 3. Calculate zone distance
    zone_dist = np.full(3, SENSOR_MAX_RANGE_MM, dtype=np.float32)
    for i, (start, end) in enumerate(SENSOR_ZONES):
        zone_values = data[:, start:end]

        # If there are valid signals in the sensor measurement
        if not np.all(np.isnan(zone_values)):
            # Calculate the 10th percentile of the values
            zone_dist[i] = np.nanpercentile(zone_values, 10)

    # 4. Calculate percentage
    return np.clip((SENSOR_FAR_MM - zone_dist) / (SENSOR_FAR_MM - SENSOR_NEAR_MM), 0, 1)


