import threading
import time

import numpy as np

from sensor.classes import SensorFrame


def make_grid(near_cols=(), near_mm=600, far_mm=3000) -> np.ndarray:
    """8x8 Distanzraster: überall weit weg, in near_cols nah."""
    grid = np.full((8, 8), far_mm, dtype=np.int16)
    for c in near_cols:
        grid[:, c] = near_mm
    return grid


class FakeSensorReader(threading.Thread):
    """
    Ersatz für SensorReader ohne Hardware (gleiche Schnittstelle:
    start(), latest(), stop()). Spielt im Kreis Szenarien durch:

        frei -> Hindernis Mitte -> Hindernis links -> Hindernis rechts
        -> alles blockiert -> Sensor-Ausfall (kein neuer Frame)

    Jedes Szenario dauert SCENARIO_S Sekunden bei 15 Hz.
    """

    FREQUENCY_HZ = 15
    SCENARIO_S = 4.0

    SCENARIOS = [
        ("frei",             ()),
        ("Hindernis Mitte",  (2, 3, 4, 5)),
        ("Hindernis links",  (0, 1, 2, 3)),
        ("Hindernis rechts", (4, 5, 6, 7)),
        ("alles blockiert",  tuple(range(8))),
        ("Sensor-Ausfall",   None),   # None = keine neuen Frames
    ]

    def __init__(self):
        super().__init__(daemon=True, name="FakeSensorReader")
        self._lock = threading.Lock()
        self._latest: SensorFrame | None = None
        self._halt = threading.Event()
        self.errors = 0
        self.current = self.SCENARIOS[0][0]

    def run(self):
        t0 = time.monotonic()
        while not self._halt.is_set():
            now = time.monotonic()
            idx = int((now - t0) / self.SCENARIO_S) % len(self.SCENARIOS)
            name, cols = self.SCENARIOS[idx]
            if name != self.current:
                self.current = name
                print(f"[FakeSensor] Szenario: {name}")
            if cols is not None:
                frame = SensorFrame(
                    t=now,
                    dist=make_grid(cols),
                    status=np.full((8, 8), 5, dtype=np.uint8),
                    sigma=np.full((8, 8), 5, dtype=np.uint16),
                )
                with self._lock:
                    self._latest = frame
            time.sleep(1.0 / self.FREQUENCY_HZ)

    def latest(self) -> SensorFrame | None:
        with self._lock:
            return self._latest

    def stop(self):
        self._halt.set()
