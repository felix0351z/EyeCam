from dataclasses import dataclass

import numpy as np


@dataclass
class SensorOutput:
    """
    Eine komplette Messung des VL53L5CX (8x8 = 64 Zonen).
    Alle Arrays haben die Form (8, 8): [Zeile, Spalte].
    """
    timestamp: float
    dist: np.ndarray     # int16,  Distanz in mm
    status: np.ndarray   # uint8,  5 / 9 = gültig, Rest verwerfen
    sigma: np.ndarray    # uint16, Messunsicherheit in mm
