import math
import socket
import struct
import time

HOST = "127.0.0.1"
PORT = 6969

class Analyzer:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.closed = False

        try:
            self.socket.connect((HOST, PORT))
        except socket.error:
            print("Failed to connect to analyzer")
            self.socket.close()
            self.closed = True

    def send_sin(self):
        if self.closed:
            return

        t0 = time.time()
        while True:

            payload = b""
            for i in range(3):
                timestamp = time.time() - t0
                label = i
                value = math.sin(timestamp * 2)

                data = struct.pack("<if", label, value)
                payload += data

            self.socket.sendall(payload)
            time.sleep(0.01) # 100 Hz

    def send(self, data: list[int]):
        if self.closed:
            return

        payload = b""
        for (i, value) in enumerate(data):
            payload += struct.pack("<if", i, value)

        self.socket.sendall(payload)




if __name__ == "__main__":
    analyzer = Analyzer()
    analyzer.send_sin()