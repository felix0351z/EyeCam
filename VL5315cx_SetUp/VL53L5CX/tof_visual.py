
import qwiic_vl53l5cx
import sys
from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

sensor = qwiic_vl53l5cx.QwiicVL53L5CX()

if sensor.is_connected() == False:
    print("Sensor nicht verbunden.", file=sys.stderr)
    sys.exit(1)

print("Initialisiere Sensor...")
if sensor.begin() == False:
    print("Initialisierung fehlgeschlagen.", file=sys.stderr)
    sys.exit(1)

sensor.set_resolution(8*8)
resolution = sensor.get_resolution()
width = int(sqrt(resolution))
sensor.start_ranging()

fig, ax = plt.subplots()
grid = np.zeros((width, width))
im = ax.imshow(grid, cmap="viridis_r", vmin=0, vmax=2000)  # 0-2000mm Farbskala
plt.colorbar(im, label="Entfernung (mm)")
ax.set_title("VL53L5CX Live-Ansicht")

def update(frame):
    if sensor.check_data_ready():
        data = sensor.get_ranging_data()
        arr = np.array(data.distance_mm).reshape(width, width)
        im.set_array(arr)
    return [im]

ani = animation.FuncAnimation(fig, update, interval=100, blit=False)
plt.show()
