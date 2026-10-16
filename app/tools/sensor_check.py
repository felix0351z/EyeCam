"""
Hardware-Check für den VL53L5CX (ohne YOLO, ohne Kamera).

Start (im Ordner app/):   python ../tools/sensor_check.py
Beenden: Strg+C

Zeigt live das 8x8-Raster in cm. Ungültige Felder (Status nicht 5/9) als '--'.
Damit prüfst du: Verkabelung, Messwerte, Orientierung, Update-Rate.
"""
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from sensor.reader import SensorReader  # noqa: E402

VALID = (5, 9)

reader = SensorReader()
reader.start()
print("Sensor läuft. Hand/Karton vor den Sensor halten. Strg+C zum Beenden.\n")

last_t, count, t0 = None, 0, time.monotonic()
try:
    while True:
        f = reader.latest()
        if f is None or f.timestamp == last_t:
            time.sleep(0.01)
            continue
        last_t = f.timestamp
        count += 1

        if count % 5 == 0:  # nicht jedes Bild ausgeben
            ok = np.isin(f.status, VALID)
            hz = count / (time.monotonic() - t0)
            print("\033[2J\033[H", end="")  # Bildschirm leeren
            print(f"Update-Rate: {hz:4.1f} Hz | gültig: {ok.sum():2d}/64 | Fehler: {reader.errors}")
            print("links <-                      -> rechts\n")
            for r in range(8):
                print(" ".join(f"{f.dist[r, c] / 10:5.0f}" if ok[r, c] else "   --" for c in range(8)))
            print("\n(Werte in cm, oben = Zeile 0)")
except KeyboardInterrupt:
    pass
finally:
    reader.stop()
