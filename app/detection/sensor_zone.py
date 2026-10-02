import logging
import time
from collections import deque
from collections.abc import Callable

import numpy as np

from detection.classes import DetectionAlgorithm
from sensor.classes import SensorFrame
from yolo.classes import YOLOOutput

log = logging.getLogger(__name__)


class SensorZoneDetection(DetectionAlgorithm):
    """
    Zonen-Erkennung auf Basis des VL53L5CX (8x8 Distanzraster).

    Das Raster wird wie die Kamera in links / mitte / rechts geteilt.
    Pro Zone wird der Anteil gültiger Felder berechnet, die näher als
    NEAR_MM sind. Über die letzten Frames wird gemittelt (Entprellen),
    die Ausweich-Entscheidung kommt aus DetectionAlgorithm._decide().

    Fällt der Sensor aus (sensor=None), wird optional auf einen
    Fallback-Algorithmus (z. B. YOLO) umgeschaltet.
    """

    MOVE_THRESHOLD = 0.5   # Anteil naher Felder in der Zone -> Hindernis
    NEAR_MM = 1500         # "nah" = unter 1,5 m (Startwert, per Analyzer tunen)
    MAX_SIGMA = 20         # Messunsicherheit in mm, darüber verwerfen
    VALID_STATUS = (5, 9)  # 6 testweise ergänzen
    WINDOW = 5             # Frames im Mittel (~0,33 s bei 15 Hz)

    # Spalten pro Zone: links 0-1, Mitte 2-5, rechts 6-7
    COLS = (slice(0, 2), slice(2, 6), slice(6, 8))
    # Zeilen, die ausgewertet werden. Falls der Sensor den Boden sieht,
    # untere Zeilen ausschließen, z. B. slice(0, 6)
    ROWS = slice(0, 8)

    WARN_INTERVAL_S = 5.0

    def __init__(self, fallback: DetectionAlgorithm | None = None):
        super().__init__()
        self._fallback = fallback
        self._percentages = [deque([0.0] * self.WINDOW, maxlen=self.WINDOW) for _ in range(3)]
        self._last_t: float | None = None
        self._last_warn = 0.0

    def add_subscriber(self, subscriber: Callable):
        super().add_subscriber(subscriber)
        if self._fallback is not None:
            self._fallback.add_subscriber(subscriber)

    def get_percentages(self):
        return np.mean(np.array(self._percentages), axis=1)

    def calculate(self, yolo_output: YOLOOutput, sensor: SensorFrame | None = None):
        if sensor is None:
            self._warn_no_sensor()
            if self._fallback is not None:
                self._fallback.calculate(yolo_output)
            return

        # Gleichen Frame nicht doppelt ins Fenster schreiben
        # (YOLO ~12 fps, Sensor 15 Hz, entkoppelt)
        if sensor.t == self._last_t:
            return
        self._last_t = sensor.t

        dist = sensor.dist[self.ROWS]
        status = sensor.status[self.ROWS]
        sigma = sensor.sigma[self.ROWS]

        valid = np.isin(status, self.VALID_STATUS) & (sigma < self.MAX_SIGMA) & (dist > 0)
        near = valid & (dist < self.NEAR_MM)

        for i, cols in enumerate(self.COLS):
            self._percentages[i].append(float(near[:, cols].mean()))

        left, middle, right = self.get_percentages()
        self._decide(left, middle, right, self.MOVE_THRESHOLD)

    def _warn_no_sensor(self):
        now = time.monotonic()
        if now - self._last_warn >= self.WARN_INTERVAL_S:
            self._last_warn = now
            log.warning("Keine aktuellen Sensordaten%s",
                        " - Fallback auf YOLO" if self._fallback else "")
