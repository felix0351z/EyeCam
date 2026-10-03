import logging
import time

from picamera2 import Picamera2

from detection.classes import MoveDirection
from detection.zone_based import ZoneBasedDetection
from sender import Sender
from sensor.reader import SensorReader
from yolo.model import YoloV5, pre_process, YoloV26

logging.basicConfig(level=logging.INFO)

MODEL_PATH = "/home/eyecam/Documents/yolo26n_ncnn_model"

# --- Einstellungen -----------------------------------------------------
USE_SENSOR_DETECTION = True      # False = nur YOLO wie bisher
MAX_SENSOR_AGE_S = 0.2           # ältere Sensordaten gelten als "kein Sensor"
USE_FAKE_SENSOR = False          # True = Testdaten ohne Hardware (siehe sensor/fake_reader.py)
# -----------------------------------------------------------------------

# Sensor ZUERST starten: Der Firmware-Upload dauert einige Sekunden
try:
    sensor_reader = SensorReader()
    sensor_reader.start()
except Exception as e:
    logging.error("Sensor nicht verfügbar, nur YOLO: %s", e)
    sensor_reader = None

picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 640)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

yolo_model = YoloV26(MODEL_PATH)
sender = Sender()

def on_detection(direction: MoveDirection):
    print(f"Move to {direction}!")

detection_algorithm = ZoneBasedDetection()
detection_algorithm.add_subscriber(on_detection)


# Measure fps
frames = 0
t_last = time.perf_counter()
last_sensor_t = None

try:
    while True:
        frame = picam2.capture_array()

        # 1. Use YOLO
        yolo_input = pre_process(frame)
        net = yolo_model.infer(yolo_input)
        yolo_output = yolo_model.post_process(frame, net, yolo_input.transform)
        # Send the YOLO Output to the analyzer
        sender.send_yolo_packet(yolo_output)


        # 2. Use Sensor
        sensor_frame = None
        if sensor_reader is not None:
            latest = sensor_reader.latest()
            # if latest is not None:
              # sender.send_sensor_packet(latest)


        # 3. Detection algorithm
        # TODO: sensor_frame im Algorithmus verwenden (aktuell nur YOLO)
        detection_algorithm.calculate(yolo_output)

        # Measure fps and print out every second
        frames += 1

        now = time.perf_counter()
        if now - t_last >= 1.0:
            print(f"{frames / (now - t_last):.1f} fps")
            frames = 0
            t_last = now
finally:
    if sensor_reader is not None:
        sensor_reader.stop()
