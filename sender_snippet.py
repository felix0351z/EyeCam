# In app/sender.py in die Klasse Sender einfügen.
# ACHTUNG: Import-Pfad und Sendemethode an send_yolo_packet angleichen!

# from api import packets_pb2
# from sensor.classes import SensorFrame

def send_sensor_packet(self, f: "SensorFrame"):
    packet = packets_pb2.Packet()
    packet.sensor.distance_mm = f.dist.astype("<i2").tobytes()
    packet.sensor.target_status = f.status.astype("<u1").tobytes()
    packet.sensor.range_sigma_mm = f.sigma.astype("<u2").tobytes()
    packet.sensor.timestamp_ms = int(f.t * 1000)

    # Genauso verschicken wie in send_yolo_packet (gleiches Framing!)
    self._send(packet)   # PLATZHALTER
