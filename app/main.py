import logging
import sys
import time

def main():
    logging.basicConfig(level=logging.INFO)

    # ---------------------------------
    # PiCam Settings
    # ---------------------------------
    from picamera2 import Picamera2

    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 640)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()


    # ---------------------------------
    # YOLO Settings
    # ---------------------------------
    from yolo.model import pre_process, YoloV26
    from tracker.tracker import Tracker
    MODEL_PATH = "/home/eyecam/yolo26n_ncnn_model"
    tracker = Tracker()

    try:
        yolo_model = YoloV26(MODEL_PATH)
    except Exception as e:
        logging.error("YOLO not available: %s", e)
        yolo_model = None


    # ---------------------------------
    # Sensor Settings
    # ---------------------------------
    from sensor.reader import SensorReader

    try:
        sensor_reader = SensorReader()
        sensor_reader.start()
    except Exception as e:
        logging.error("Sensor not available: %s", e)
        sensor_reader = None


    # ---------------------------------
    # Algorithm & Sender Settings
    # ---------------------------------
    from detection.classes import MoveDirection
    from detection.zone_based import ZoneDetection
    from sender import Sender
    from detection.buzz_motors import BuzzController

    sender = Sender()

    buzz = BuzzController()
    buzz.start()

    def on_detection(direction: MoveDirection):
        print(f"Move to {direction}!")

    detection_algorithm = ZoneDetection()
    detection_algorithm.add_subscriber(on_detection)
    detection_algorithm.add_subscriber(buzz.notify)
    detection_algorithm.add_subscriber(sender.send_move_packet)



    # ---------------------------------
    # Main loop
    # ---------------------------------

    if (yolo_model is None) and (sensor_reader is None):
        sys.exit("YOLO and Sensor not available.")

    # Limit the frame rate to save power (None = no limit)
    MAX_FPS = 7

    # Measure FPS rate
    frames = 0
    t_last = time.perf_counter()

    try:
        # Runs until the analyzer sends a shutdown command
        while not sender.shutdown.is_set():
            # Paused by the analyzer
            if not sender.running.wait(1):
                continue

            t_start = time.perf_counter()
            frame = picam2.capture_array()

            # 1. Use YOLO and track the boxes
            yolo_output = None
            track_ids = None
            if yolo_model is not None:
                yolo_input = pre_process(frame)
                net = yolo_model.infer(yolo_input)
                yolo_output = yolo_model.post_process(frame, net, yolo_input.transform)

                track_ids = tracker.update(yolo_output, frame.shape)
                sender.send_yolo_packet(yolo_output)


            # 2. Use the Sensor
            sensor_frame = None
            if sensor_reader is not None:
                sensor_frame = sensor_reader.latest()
                if sensor_frame is not None:
                    sender.send_sensor_packet(sensor_frame)

            # 3. Detection algorithm
            danger_values = detection_algorithm.calculate(yolo_output, sensor_frame)
            sender.send_graph_packet(danger_values)

            # 4. Limit the frame rate
            if MAX_FPS is not None:
                remaining = 1 / MAX_FPS - (time.perf_counter() - t_start)
                if remaining > 0:
                    time.sleep(remaining)

            # 5. Measure fps and print out every second
            frames += 1
            now = time.perf_counter()
            if now - t_last >= 1.0:
                print(f"{frames / (now - t_last):.1f} fps")
                frames = 0
                t_last = now

    finally:
        logging.info("Shutting down EyeCam ...")
        buzz.stop()
        if sensor_reader is not None:
            sensor_reader.stop()
        picam2.stop()

if __name__ == "__main__":
    main()