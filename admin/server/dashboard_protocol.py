import json

class Protocol:
    def __init__(self):
        self.encoding = "utf-8"
        self.delimiter = '\n'

    def send_message(self, client_socket, message):
        json_data = json.dumps(message, ensure_ascii=False)

        data = json_data + self.delimiter

        client_socket.sendall(data.encode(self.encoding))

    def receive_message(self, client_socket, buffer):

        data = client_socket.recv(1024)

        if not data:
            return buffer, [], False

        buffer += data.decode(self.encoding)
        messages = []

        while self.delimiter in buffer:
            raw_message, buffer = buffer.split(self.delimiter, 1)

            if raw_message.strip():
                message = json.loads(raw_message)
                messages.append(message)

        return buffer, messages, True


