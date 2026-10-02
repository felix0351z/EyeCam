"""Prüft, dass Sender- und Analyzer-Seite dasselbe Byte-Layout nutzen."""
import numpy as np
import pytest

from sensor.fake_reader import make_grid


def encode(dist, status, sigma):
    return (dist.astype("<i2").tobytes(),
            status.astype("<u1").tobytes(),
            sigma.astype("<u2").tobytes())


def decode(b_dist, b_status, b_sigma):
    return (np.frombuffer(b_dist, dtype="<i2").reshape(8, 8),
            np.frombuffer(b_status, dtype="<u1").reshape(8, 8),
            np.frombuffer(b_sigma, dtype="<u2").reshape(8, 8))


def sample():
    rng = np.random.default_rng(1)
    dist = rng.integers(-1, 4000, (8, 8)).astype(np.int16)
    status = rng.choice([5, 6, 9, 255], (8, 8)).astype(np.uint8)
    sigma = rng.integers(0, 60000, (8, 8)).astype(np.uint16)
    return dist, status, sigma


def test_sizes():
    b = encode(*sample())
    assert [len(x) for x in b] == [128, 64, 128]


def test_numpy_roundtrip():
    d, s, g = sample()
    d2, s2, g2 = decode(*encode(d, s, g))
    assert (d == d2).all() and (s == s2).all() and (g == g2).all()


def test_protobuf_roundtrip():
    pb = pytest.importorskip("api.packets_pb2")
    if "timestamp_ms" not in pb.SensorPacket.DESCRIPTOR.fields_by_name:
        pytest.skip("packets_pb2 wurde noch nicht neu generiert")
    d, s, g = sample()
    msg = pb.Packet()
    msg.sensor.distance_mm, msg.sensor.target_status, msg.sensor.range_sigma_mm = encode(d, s, g)
    msg.sensor.timestamp_ms = 123456
    raw = msg.SerializeToString()

    back = pb.Packet()
    back.ParseFromString(raw)
    d2, s2, g2 = decode(back.sensor.distance_mm, back.sensor.target_status, back.sensor.range_sigma_mm)
    assert (d == d2).all() and (s == s2).all() and (g == g2).all()
    assert back.sensor.timestamp_ms == 123456
