## Python
import qwiic_vl53l5cx
import sys
from math import sqrt
import time

def runExample():
    print("Qwiic VL53L5CX Test")

    sensor = qwiic_vl53l5cx.QwiicVL53L5CX()

    if sensor.is_connected() == False:
        print("Sensor nicht verbunden. Verkabelung prüfen.", file=sys.stderr)
        return

    print("Initialisiere Sensor. Kann bis zu 10s dauern...")
    if sensor.begin() == False:
        print("Initialisierung fehlgeschlagen.", file=sys.stderr)
        sys.exit(1)

    sensor.set_resolution(8*8)
    resolution = sensor.get_resolution()
    width = int(sqrt(resolution))
    sensor.start_ranging()

    while True:
        if sensor.check_data_ready():
            data = sensor.get_ranging_data()
            for y in range(0, (width * (width - 1)) + 1, width):
                for x in range(width - 1, -1, -1):
                    print(data.distance_mm[x + y], end="\t")
                print()
            print()
        time.sleep(0.05)

if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        print("\nBeendet")
        sys.exit(0)