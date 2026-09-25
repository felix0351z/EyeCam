import socket


class Sender:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.closed = False

        try:
            socket.connect(("192.168.178.100", 6969))
        except socket.error:
            print("Failed to connect to analyzer")
            socket.close()
            closed = True

    def send(self, ):
