"""
Tests ohne Hardware. Ausführen (im Repo-Root):

    pip install pytest numpy
    cd app && python -m pytest ../tests -v
"""
import numpy as np
import pytest

from detection.classes import MoveDirection
from detection.sensor_zone import SensorZoneDetection
from sensor.classes import SensorFrame
from sensor.fake_reader import make_grid


class Recorder:
    def __init__(self):
        self.moves = []

    def __call__(self, direction):
        self.moves.append(direction)


@pytest.fixture
def det():
    d = SensorZoneDetection()
    d._last_move = -100.0  # Cooldown (2 s nach Start) für Tests aufheben
    rec = Recorder()
    d.add_subscriber(rec)
    d.rec = rec
    return d


_t = [0.0]


def frame(dist, status=5, sigma=5):
    _t[0] += 1.0 / 15
    return SensorFrame(
        t=_t[0],
        dist=dist,
        status=np.full((8, 8), status, dtype=np.uint8),
        sigma=np.full((8, 8), sigma, dtype=np.uint16),
    )


def feed(det, f, n=5):
    for i in range(n):
        # jedes Mal ein neuer Zeitstempel, sonst zählt es als Duplikat
        g = SensorFrame(t=_t[0] + (i + 1) / 15, dist=f.dist, status=f.status, sigma=f.sigma)
        det.calculate(None, g)
    _t[0] += n / 15


def test_free_path_no_move(det):
    feed(det, frame(make_grid(())))
    assert det.rec.moves == []


def test_middle_blocked_left_free_goes_left(det):
    feed(det, frame(make_grid((2, 3, 4, 5, 6, 7))))   # Mitte + rechts blockiert
    assert det.rec.moves == [MoveDirection.LEFT]


def test_middle_blocked_right_free_goes_right(det):
    feed(det, frame(make_grid((0, 1, 2, 3, 4, 5))))   # links + Mitte blockiert
    assert det.rec.moves == [MoveDirection.RIGHT]


def test_everything_blocked_stops(det):
    feed(det, frame(make_grid(range(8))))
    assert det.rec.moves == [MoveDirection.STOP]


def test_invalid_status_is_ignored(det):
    feed(det, frame(make_grid(range(8)), status=255))  # "kein Target"
    assert det.rec.moves == []


def test_high_sigma_is_ignored(det):
    feed(det, frame(make_grid(range(8)), sigma=500))
    assert det.rec.moves == []


def test_far_objects_are_ignored(det):
    feed(det, frame(make_grid(range(8), near_mm=2500)))  # > NEAR_MM
    assert det.rec.moves == []


def test_single_outlier_frame_does_not_trigger(det):
    feed(det, frame(make_grid(())), n=4)
    feed(det, frame(make_grid(range(8))), n=1)  # ein einziger Ausreißer
    assert det.rec.moves == []


def test_duplicate_frame_is_not_counted_twice(det):
    f = frame(make_grid(range(8)))
    for _ in range(10):
        det.calculate(None, f)   # immer derselbe Zeitstempel
    # Nur 1 Frame im Fenster -> Mittel 0.2 -> kein Alarm
    assert det.rec.moves == []


def test_no_sensor_uses_fallback():
    calls = []

    class FakeFallback:
        def add_subscriber(self, s):
            pass

        def calculate(self, yolo_output):
            calls.append(yolo_output)

    d = SensorZoneDetection(fallback=FakeFallback())
    d.calculate("yolo", None)
    assert calls == ["yolo"]
