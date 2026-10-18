import logging
import queue
import socket
import struct
import threading
import time

import numpy as np
import simplejpeg

from api import packets_pb2
from detection.classes import DangerValues
from sensor.classes import SensorOutput
from yolo.classes import YOLOOutput

log = logging.getLogger(__name__)
LISTEN_ADDRESS = ("0.0.0.0", 6969)
SEND_TIMEOUT = 2.0 # seconds

def _encode_jpeg(image: np.ndarray):
    return simplejpeg.encode_jpeg(image, quality=80, colorspace="BGR")

class Sender:
    """
    Create a server for an analyzer connection.
    The server sends packets to the analyzer in a background thread.

    If the analyzer is not connected, packets are dropped. A lost connection is
    re-established automatically.
    """

    def __init__(self):
        self._queue = queue.Queue(maxsize=10)
        self._connected = threading.Event()
        threading.Thread(target=self._run, name="Sender", daemon=True).start()

    def _run(self):
        server = socket.create_server(LISTEN_ADDRESS)
        log.info("Waiting for analyzer on port %d", LISTEN_ADDRESS[1])

        while True:
            sock, address = server.accept()
            sock.settimeout(SEND_TIMEOUT)
            self._clear_queue()
            self._connected.set()
            log.info("Analyzer connected from %s", address[0])

            try:
                while True:
                    sock.sendall(self._queue.get())
            except OSError as e:
                log.info("Analyzer disconnected (%s)", e)
            finally:
                self._connected.clear()
                sock.close()

    @property
    def connected(self):
        return self._connected.is_set()

    def _clear_queue(self):
        while not self._queue.empty():
            self._queue.get_nowait()


    def _send(self, packet: packets_pb2.Packet):
        payload = packet.SerializeToString()

        try:
            # 4 byte length prefix (big endian) + protobuf payload
            self._queue.put_nowait(struct.pack("!I", len(payload)) + payload)
        except queue.Full:
            # Analyzer too slow, drop packet
            pass

    def send_yolo_packet(self, data: YOLOOutput):
        if not self.connected:
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
        if not self.connected:
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
        if not self.connected:
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