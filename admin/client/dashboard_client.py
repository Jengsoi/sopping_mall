import socket
import threading

from PySide6.QtCore import QObject, Signal
from client.dashboard_protocol import Protocol

class NetworkClient(QObject):

    data_receive = Signal(dict)
    connection_error = Signal(str)

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.proto = Protocol()

    def start(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))

        except OSError as error:
            self.connection_error.emit(str(error))
            return

        receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        receive_thread.start()

    def receive_loop(self):

        buffer = ""

        while True:

            buffer, messages, connected = self.proto.receive_message(self.sock, buffer)

            if not connected:
                break

            for message in messages:
                self.data_receive.emit(message)


    def send_request(self, start, end):
        if self.sock is None:
            return

        self.proto.send_message(self.sock,{
            "type" : "data",
            "start" : start,
            "end" : end
        })

