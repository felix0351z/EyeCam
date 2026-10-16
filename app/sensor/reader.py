import logging
import time
import multiprocessing as mp

import numpy as np

from sensor.classes import SensorOutput

log = logging.getLogger(__name__)

SIZE = 8
GRID_SIZE = SIZE * SIZE
FREQUENCY_HZ = 15
FLIP_UD = False
FLIP_LR = False

# Frames older than this are treated as missing (e.g. sensor process crashed)
MAX_AGE_S = 0.2

# numpy dtype structure for a shared-memory buffer
_FRAME_DTYPE = np.dtype([
    ("timestamp", np.float64),
    ("dist", np.int16, (SIZE, SIZE)),
    ("status", np.uint8, (SIZE, SIZE)),
    ("sigma", np.uint16, (SIZE, SIZE)),
])


def _to_grid(values, dtype) -> np.ndarray:
    grid = np.asarray(values[:GRID_SIZE], dtype=dtype).reshape(SIZE, SIZE)
    if FLIP_UD:
        grid = np.flipud(grid)
    if FLIP_LR:
        grid = np.fliplr(grid)
    return grid

def _start_sensor_process(buf, lock, ready, stop):
    """
    Start a new process to read data from the sensor.
    """
    logging.basicConfig(level=logging.INFO)
    import qwiic_vl53l5cx

    sensor = qwiic_vl53l5cx.QwiicVL53L5CX()
    if not sensor.is_connected():
        log.error("VL53L5CX not found on I2C bus.")
        return

    sensor.begin()
    sensor.set_resolution(GRID_SIZE)
    sensor.set_ranging_frequency_hz(FREQUENCY_HZ)
    sensor.start_ranging()
    ready.set()

    frame = np.frombuffer(buf, dtype=_FRAME_DTYPE, count=1)[0]
    try:
        while not stop.is_set():
            try:
                if not sensor.check_data_ready():
                    time.sleep(0.002)
                    continue
                t = time.monotonic()
                d = sensor.get_ranging_data()
                with lock:
                    frame["timestamp"] = t
                    frame["dist"] = _to_grid(d.distance_mm, np.int16)
                    frame["status"] = _to_grid(d.target_status, np.uint8)
                    frame["sigma"] = _to_grid(d.range_sigma_mm, np.uint16)
            except Exception:
                log.exception("Sensor reading failed")
                time.sleep(1)

    finally:
        sensor.stop_ranging()


class SensorReader:
    """
    """

    def __init__(self):
        ctx = mp.get_context("spawn")
        self._buf = ctx.RawArray("B", _FRAME_DTYPE.itemsize)
        self._lock = ctx.Lock()
        self._ready = ctx.Event()
        self._stop = ctx.Event()

        self._process = ctx.Process(
            target=_start_sensor_process, name="SensorReader", daemon=True,
            args=(self._buf, self._lock, self._ready, self._stop)
        )

    def start(self, timeout: float = 15.0):
        """
        Start the sensor process and wait for the ready event.
        If it won't be ready within the timeout raise an exception.
        """

        log.info("Starting sensor, loading firmware...")
        self._process.start()

        if not self._ready.wait(timeout=timeout):
            self.stop()
            raise RuntimeError("Sensor not ready. Is it connected?")


    def latest(self) -> SensorOutput | None:
        """
        Get the latest frame from the sensor.
        Returns None if there is no frame younger than MAX_AGE_S.
        """

        with self._lock:
            f = np.frombuffer(self._buf, dtype=_FRAME_DTYPE, count=1)[0].copy()

        # Before the first frame the timestamp is 0.0, so this also returns None
        if time.monotonic() - f["timestamp"] > MAX_AGE_S:
            return None

        return SensorOutput(timestamp=float(f["timestamp"]),
                            dist=f["dist"],
                            status=f["status"],
                            sigma=f["sigma"]
        )



    def stop(self):
        """
        Stop the sensor reading process.
        """
        self._stop.set()
        self._process.join(timeout=5)

        # If the process has not finished after the timeout,
        # force the cancellation.
        if self._process.is_alive():
            self._process.terminate()