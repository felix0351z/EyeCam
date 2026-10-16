import socket
import struct
import time

import numpy as np
import simplejpeg

from api import packets_pb2
from detection.classes import DangerValues
from sensor.classes import SensorOutput
from yolo.classes import YOLOOutput


def _encode_jpeg(image: np.ndarray):
    return simplejpeg.encode_jpeg(image, quality=80, colorspace="BGR")

class Sender:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.closed = False

        try:
            self.socket.connect(("192.168.178.100", 6969))
        except socket.error:
            print("Failed to connect to analyzer")
            self.socket.close()
            self.closed = True


    def _send(self, packet: packets_pb2.Packet):
        payload = packet.SerializeToString()
        self.socket.sendall(struct.pack("!I", len(payload)) + payload)  # 4 Byte Länge (Big Endian)


    def send_yolo_packet(self, data: YOLOOutput):
        if self.closed:
            return

        packet = packets_pb2.Packet(
            yolo=packets_pb2.YoloPacket(
                frame_id=0,
                timestamp_ms=int(time.time() * 1000),
                jpeg_bytes=_encode_jpeg(data.image),
                confidences=np.ascontiguousarray(data.confidences, dtype='<f4').tobytes(),
                class_ids=np.ascontiguousarray(data.class_ids, dtype='<i4').tobytes(),
                boxes=np.ascontiguousarray(data.boxes, dtype='<f4').tobytes()
            )
        )

        self._send(packet)

    def send_sensor_packet(self, data: SensorOutput):
        if self.closed:
            return

        packet = packets_pb2.Packet(
            sensor=packets_pb2.SensorPacket(
                distance_mm=np.ascontiguousarray(data.dist, dtype='<i2').tobytes(),
                target_status=np.ascontiguousarray(data.status, dtype='<u1').tobytes(),
                range_sigma_mm=np.ascontiguousarray(data.sigma, dtype='<u2').tobytes(),
            )
        )

        self._send(packet)

    def send_graph_packet(self, data: DangerValues):
        if self.closed:
            return

        # Labels in the order [left, middle, right], like the danger arrays
        yolo_labels = (packets_pb2.YOLO_LEFT, packets_pb2.YOLO_MIDDLE, packets_pb2.YOLO_RIGHT)
        sensor_labels = (packets_pb2.SENSOR_LEFT, packets_pb2.SENSOR_MIDDLE, packets_pb2.SENSOR_RIGHT)

        graphs = [
            packets_pb2.GraphValue(name=label, value=float(value))
            for labels, values in ((yolo_labels, data.yolo), (sensor_labels, data.sensor))
            for label, value in zip(labels, values)
        ]

        packet = packets_pb2.Packet(
            graph=packets_pb2.GraphPacket(frame_id=0, graphs=graphs)
        )

        self._send(packet)