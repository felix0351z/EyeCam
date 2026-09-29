import time

from picamera2 import Picamera2

from detection.classes import DodgeDirection
from detection.zone_based import ZoneBasedDetection
from sender import Sender
from yolo.model import YoloV5, pre_process, YoloV26

MODEL_PATH = "/home/eyecam/Documents/yolo26n_ncnn_model"

picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 640)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

yolo_model = YoloV26(MODEL_PATH)
sender = Sender()

def on_detection(direction: DodgeDirection):
    print(f"Move to ${direction}!")

detection_algorithm = ZoneBasedDetection()
detection_algorithm.add_subscriber(on_detection)


# Measure fps
frames = 0
t_last = time.perf_counter()

while True:
    frame = picam2.capture_array()

    # Use YOLO
    yolo_input = pre_process(frame)
    net = yolo_model.infer(yolo_input)
    yolo_output = yolo_model.post_process(frame, net, yolo_input.transform)

    # TODO Use Sensor

    # Send the YOLO Output to the analyzer
    sender.send_yolo_packet(yolo_output)

    # Detection algorithm
    detection_algorithm.check(yolo_output)

    # Measure fps and print out every second
    frames += 1

    now = time.perf_counter()
    if now - t_last >= 1.0:
        print(f"{frames / (now - t_last):.1f} fps")
        frames = 0
        t_last = now