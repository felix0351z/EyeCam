"""
Laptop-Demo ohne Kamera, YOLO und Sensor.

Start (im Ordner app/):   python ../tools/fake_demo.py
Beenden: Strg+C (sonst läuft ein Durchgang aller Szenarien und endet).

Der Fake-Sensor spielt Szenarien ab, die echte Erkennung (SensorZoneDetection)
wertet sie aus. Erwartung steht im Szenario-Namen (siehe sensor/fake_reader.py).
"""
import logging
import sys
import time

sys.path.insert(0, ".")
from detection.sensor_zone import SensorZoneDetection  # noqa: E402
from sensor.fake_reader import FakeSensorReader  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="   ! %(message)s")
MAX_SENSOR_AGE_S = 0.2

reader = FakeSensorReader()
detection = SensorZoneDetection()
detection.add_subscriber(lambda d: print(f"   -> Move to {d.name}"))

reader.start()
end = time.monotonic() + len(reader.SCENARIOS) * reader.SCENARIO_S
print("Demo läuft (ein Durchgang aller Szenarien) ...\n")
try:
    while time.monotonic() < end:
        frame = reader.latest()
        if frame is not None and time.monotonic() - frame.t > MAX_SENSOR_AGE_S:
            frame = None          # wie in main.py: zu alt = kein Sensor
        detection.calculate(None, frame)
        time.sleep(1 / 12)        # ungefähr YOLO-Takt
except KeyboardInterrupt:
    pass
finally:
    reader.stop()
print("\nFertig.")
