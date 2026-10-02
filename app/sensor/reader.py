import logging
import threading
import time

import numpy as np
import qwiic_vl53l5cx

from sensor.classes import SensorFrame

log = logging.getLogger(__name__)


class SensorReader(threading.Thread):
    """
    Liest den VL53L5CX in einem eigenen Thread aus ("Briefkasten").

    Der Thread legt immer nur den NEUESTEN Frame ab. Die Hauptschleife
    (YOLO) holt ihn per latest() ab, wenn sie Zeit hat, und wird nie
    vom langsamen I2C-Bus ausgebremst.
    """

    SIZE = 8
    FREQUENCY_HZ = 15

    # Orientierung: Je nach Einbaulage ist das Raster gedreht/gespiegelt.
    # Mit der Testhand prüfen und hier anpassen! (Hand links -> Spalten 0-1 aktiv)
    FLIP_UD = False
    FLIP_LR = False

    def __init__(self):
        super().__init__(daemon=True, name="SensorReader")

        self._sensor = qwiic_vl53l5cx.QwiicVL53L5CX()
        if not self._sensor.is_connected():
            raise RuntimeError("VL53L5CX nicht gefunden (I2C-Verkabelung prüfen)")

        log.info("Lade Sensor-Firmware, das dauert einige Sekunden ...")
        self._sensor.begin()
        self._sensor.set_resolution(self.SIZE * self.SIZE)
        self._sensor.set_ranging_frequency_hz(self.FREQUENCY_HZ)
        self._sensor.start_ranging()

        self._lock = threading.Lock()
        self._latest: SensorFrame | None = None
        self._halt = threading.Event()
        self.errors = 0

    def _to_grid(self, values, dtype) -> np.ndarray:
        n = self.SIZE * self.SIZE
        grid = np.asarray(values[:n], dtype=dtype).reshape(self.SIZE, self.SIZE)
        if self.FLIP_UD:
            grid = np.flipud(grid)
        if self.FLIP_LR:
            grid = np.fliplr(grid)
        return np.ascontiguousarray(grid)

    def run(self):
        while not self._halt.is_set():
            try:
                if self._sensor.check_data_ready():
                    d = self._sensor.get_ranging_data()
                    frame = SensorFrame(
                        t=time.monotonic(),
                        dist=self._to_grid(d.distance_mm, np.int16),
                        status=self._to_grid(d.target_status, np.uint8),
                        sigma=self._to_grid(d.range_sigma_mm, np.uint16),
                    )
                    with self._lock:
                        self._latest = frame
                else:
                    time.sleep(0.002)
            except Exception:
                # Ein Lesefehler darf den Thread nicht beenden
                self.errors += 1
                log.exception("Sensor-Lesefehler (#%d)", self.errors)
                time.sleep(0.1)

    def latest(self) -> SensorFrame | None:
        with self._lock:
            return self._latest

    def stop(self):
        self._halt.set()
        self.join(timeout=1.0)
        try:
            self._sensor.stop_ranging()
        except Exception:
            log.exception("stop_ranging fehlgeschlagen")
