import json
import socket
import threading

from PySide6.QtCore import QObject, Signal


HOST = "127.0.0.1"
PORT = 6000

# 서버와 동일한 메시지 구분자 (서버의 MESSAGE_DELIMITER와 일치해야 함)
MESSAGE_DELIMITER = b"\n"


class Client(QObject):
    # 서버 연결 성공 시 발생
    connected = Signal()

    # 서버 연결 종료 시 발생
    disconnected = Signal()

    # 서버 응답을 받았을 때 발생
    message_received = Signal(dict)

    # 통신 오류 발생 시 오류 내용을 전달
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()

        # 서버 주소와 포트 저장
        self.host = HOST
        self.port = PORT

        # 서버 통신에 사용할 소켓
        self.client_socket = None

        # 메시지 수신 스레드 실행 여부
        self.running = False

        # 메시지 수신에 사용할 스레드
        self.receive_thread = None

        # 소켓에서 받은 데이터 중 아직 처리하지 않은 부분
        self.buffer = ""

    # 서버에 연결
    def connect_server(self):
        # 이미 연결되어 있다면 다시 연결하지 않음
        if self.running:
            return

        try:
            # TCP 소켓 생성
            self.client_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            # 서버에 연결
            self.client_socket.connect(
                (
                    self.host,
                    self.port
                )
            )

            # 수신 반복문 실행 상태로 변경
            self.running = True

            # 이전 연결에서 남은 데이터가 없도록 버퍼 초기화
            self.buffer = ""

            # 서버 응답을 별도 스레드에서 수신
            self.receive_thread = threading.Thread(
                target=self.receive_loop,
                daemon=True
            )

            self.receive_thread.start()

            # UI에 서버 연결 성공 전달
            self.connected.emit()

        except ConnectionRefusedError:
            self.close_socket()

            self.error_occurred.emit(
                "서버에 연결할 수 없습니다."
            )

        except OSError as error:
            self.close_socket()

            self.error_occurred.emit(
                f"서버 연결 중 오류가 발생했습니다: {error}"
            )

    # 딕셔너리를 JSON으로 변환해서 서버에 전송
    def send_message(self, message):
        # 서버 연결 상태 확인
        if not self.running or self.client_socket is None:
            self.error_occurred.emit(
                "서버에 연결되어 있지 않습니다."
            )
            return False

        try:
            # 딕셔너리를 JSON 바이트로 변환
            json_data = json.dumps(
                message,
                ensure_ascii=False
            ).encode("utf-8")

            # JSON 본문 뒤에 구분자를 붙여서 전송
            self.client_socket.sendall(
                json_data + MESSAGE_DELIMITER
            )

            return True

        except OSError as error:
            self.error_occurred.emit(
                f"메시지 전송 중 오류가 발생했습니다: {error}"
            )

            return False

    # 서버에서 메시지 하나 수신
    # 구분자(\n)가 나올 때까지 소켓에서 데이터를 받아 버퍼에 쌓는다
    def receive_message(self):
        while self.running:
            # 버퍼에 이미 완성된 메시지가 있는 경우
            if MESSAGE_DELIMITER.decode("utf-8") in self.buffer:
                json_data, self.buffer = self.buffer.split(
                    MESSAGE_DELIMITER.decode("utf-8"),
                    1
                )

                # 메시지 길이가 올바른지 검사
                if len(json_data) <= 0:
                    raise ValueError(
                        "메시지 길이가 올바르지 않습니다."
                    )

                # JSON 바이트를 딕셔너리로 변환
                return json.loads(json_data)

            # 소켓에서 데이터 수신
            data = self.client_socket.recv(4096)

            # 서버가 연결을 종료한 경우
            if not data:
                return None

            # 받은 데이터를 문자열로 변환해 버퍼에 추가
            self.buffer += data.decode("utf-8")

        return None

    # 서버 응답을 계속 기다리는 수신 반복문
    def receive_loop(self):
        try:
            while self.running:
                response = self.receive_message()

                # 서버 연결이 종료된 경우
                if response is None:
                    break

                # 받은 응답을 UI로 전달
                self.message_received.emit(
                    response
                )

        except ConnectionResetError:
            if self.running:
                self.error_occurred.emit(
                    "서버와의 연결이 종료되었습니다."
                )

        except json.JSONDecodeError:
            if self.running:
                self.error_occurred.emit(
                    "서버 응답을 JSON으로 변환하지 못했습니다."
                )

        except OSError as error:
            if self.running:
                self.error_occurred.emit(
                    f"메시지 수신 중 오류가 발생했습니다: {error}"
                )

        except Exception as error:
            if self.running:
                self.error_occurred.emit(
                    f"클라이언트 오류가 발생했습니다: {error}"
                )

        finally:
            self.running = False
            self.close_socket()

            # UI에 연결 종료 전달
            self.disconnected.emit()

    # 서버 연결 종료
    def disconnect_server(self):
        self.running = False
        self.close_socket()

    # 소켓 종료
    def close_socket(self):
        if self.client_socket is None:
            return

        try:
            # 송수신 종료
            self.client_socket.shutdown(
                socket.SHUT_RDWR
            )

        except OSError:
            pass

        try:
            # 소켓 닫기
            self.client_socket.close()

        except OSError:
            pass

        self.client_socket = None