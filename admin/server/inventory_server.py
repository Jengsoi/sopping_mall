import json
import socket
import threading

from inventory_logic import Inventory

HOST = "127.0.0.1"
PORT = 6000

# 메시지 본문의 끝을 표시하는 구분자
MESSAGE_DELIMITER = b"\n"
# 서버에서 허용할 최대 메시지 크기
MAX_MESSAGE_SIZE = 10 * 1024 * 1024

class Server:
    def __init__(self):
        # 서버 주소와 포트
        self.host = HOST
        self.port = PORT

        # 서버 실행에 사용할 소켓
        self.server_socket = None

        # 서버 실행 상태
        self.running = False

        # 재고관리 기능을 처리할 객체
        self.inventory = Inventory()

        # Inventory 클래스에서 처리할 요청 타입
        self.inventory_request_types = {
            "category_list",
            "category_add",
            "category_update",
            "inventory_product_list",
            "product_add",
            "product_update",
            "stock_decrease"
        }

    # 딕셔너리를 JSON 바이트로 변환해서 클라이언트에 전송
    def send_message(self, client_socket, message):
        try:
            # 딕셔너리를 JSON 문자열로 변환한 후 바이트로 변환
            json_data = json.dumps(
                message,
                ensure_ascii=False
            ).encode("utf-8")

            # JSON 본문 뒤에 구분자를 붙여서 전송
            client_socket.sendall(
                json_data + MESSAGE_DELIMITER
            )

            return True

        except TypeError as error:
            print(f"[JSON 변환 오류] {error}")
            return False

        except OSError as error:
            print(f"[메시지 전송 오류] {error}")
            return False

    # 소켓에서 받은 데이터를 버퍼에 쌓아가며
    # 구분자(\n) 단위로 완성된 메시지들을 꺼내서 반환
    def receive_message(self, client_socket, buffer):
        messages = []

        # 소켓에서 데이터 수신
        data = client_socket.recv(4096)

        # 클라이언트가 연결을 종료한 경우
        if not data:
            return buffer, messages, False

        # 받은 데이터를 문자열로 변환해 버퍼에 추가
        buffer += data.decode("utf-8")

        # 지나치게 큰 메시지 수신 방지
        if len(buffer) > MAX_MESSAGE_SIZE:
            raise ValueError(
                "허용 가능한 메시지 크기를 초과했습니다."
            )

        # 버퍼에 구분자가 있는 만큼 완성된 메시지를 꺼내서 처리
        while MESSAGE_DELIMITER.decode("utf-8") in buffer:
            json_data, buffer = buffer.split(
                MESSAGE_DELIMITER.decode("utf-8"),
                1
            )

            # 메시지 길이가 올바른지 검사
            if len(json_data) <= 0:
                raise ValueError(
                    "메시지 길이가 올바르지 않습니다."
                )

            # JSON 문자열을 Python 딕셔너리로 변환
            message = json.loads(json_data)

            # 요청 데이터가 딕셔너리인지 검사
            if not isinstance(message, dict):
                raise ValueError(
                    "클라이언트 요청 형식이 올바르지 않습니다."
                )

            messages.append(message)

        return buffer, messages, True

    # 로그인 요청 처리
    # 현재는 서버 구조 확인용 임시 로그인 코드
    # 로그인 담당자의 실제 기능이 완성되면 이 메서드를 교체
    def handle_login(self, request):
        # 클라이언트가 입력한 아이디와 비밀번호 가져오기
        login_id = request.get(
            "login_id",
            ""
        ).strip()

        password = request.get(
            "password",
            ""
        )

        # 아이디 빈칸 검사
        if not login_id:
            return {
                "type": "login",
                "success": False,
                "message": "아이디를 입력하세요."
            }

        # 비밀번호 빈칸 검사
        if not password:
            return {
                "type": "login",
                "success": False,
                "message": "비밀번호를 입력하세요."
            }

        # 서버 기능 확인을 위한 임시 계정
        # 실제 프로젝트에서는 회원 테이블을 조회하도록 변경
        test_accounts = {
            "admin": "1234",
            "user01": "1234"
        }

        # 입력한 아이디에 해당하는 비밀번호 가져오기
        saved_password = test_accounts.get(
            login_id
        )

        # 등록되지 않은 아이디이거나 비밀번호가 다른 경우
        if saved_password is None or saved_password != password:
            return {
                "type": "login",
                "success": False,
                "message": "아이디 또는 비밀번호가 올바르지 않습니다."
            }

        # 로그인 성공 응답
        return {
            "type": "login",
            "success": True,
            "login_id": login_id,
            "is_admin": login_id == "admin",
            "message": "로그인에 성공했습니다."
        }

    # 재고관리 요청 처리
    def handle_inventory_request(
        self,
        client_socket,
        request,
        login_id
    ):
        request_type = request.get(
            "type",
            ""
        )

        # 로그인하지 않은 사용자의 재고관리 요청 거부
        if login_id is None:
            response = {
                "type": request_type,
                "success": False,
                "message": "로그인이 필요합니다."
            }

            self.send_message(
                client_socket,
                response
            )

            return

        # 재고관리 요청과 로그인 ID를 Inventory 객체에 전달
        response = self.inventory.handle_request(
            request,
            login_id
        )

        # 처리 결과를 클라이언트에 전송
        self.send_message(
            client_socket,
            response
        )

    # 클라이언트 한 명의 요청을 반복해서 처리
    def handle_client(
            self,
            client_socket,
            client_address
    ):
        print(f"[클라이언트 접속] {client_address}")

        # 로그인 기능 구현 전까지 접속한 사용자를 임시 관리자로 처리
        login_id = "admin"

        # 소켓에서 받은 데이터 중 아직 처리하지 않은 부분
        buffer = ""

        try:
            with client_socket:
                while self.running:
                    # 클라이언트 요청 수신
                    buffer, requests, connected = self.receive_message(
                        client_socket,
                        buffer
                    )

                    # 클라이언트 연결이 종료된 경우
                    if not connected:
                        break

                    for request in requests:
                        print(
                            f"[요청] {client_address}: "
                            f"{request}"
                        )

                        # 요청 타입 가져오기
                        request_type = request.get(
                            "type",
                            ""
                        )

                        # 요청 타입이 없는 경우
                        if not request_type:
                            response = {
                                "type": "error",
                                "success": False,
                                "message": "요청 타입이 필요합니다."
                            }

                            self.send_message(
                                client_socket,
                                response
                            )

                            continue

                        # 로그인 요청 처리
                        if request_type == "login":
                            response = self.handle_login(
                                request
                            )

                            if response.get("success"):
                                login_id = response.get(
                                    "login_id"
                                )

                            self.send_message(
                                client_socket,
                                response
                            )

                            continue

                        # 로그아웃 요청 처리
                        if request_type == "logout":
                            login_id = None

                            response = {
                                "type": "logout",
                                "success": True,
                                "message": "로그아웃되었습니다."
                            }

                            self.send_message(
                                client_socket,
                                response
                            )

                            continue

                        # 재고관리 요청 처리
                        if request_type in self.inventory_request_types:
                            self.handle_inventory_request(
                                client_socket,
                                request,
                                login_id
                            )

                            continue

                        # 지원하지 않는 요청
                        response = {
                            "type": "error",
                            "success": False,
                            "message": (
                                f"지원하지 않는 요청입니다: "
                                f"{request_type}"
                            )
                        }

                        self.send_message(
                            client_socket,
                            response
                        )

        except ConnectionResetError:
            print(
                f"[클라이언트 연결 강제 종료] "
                f"{client_address}"
            )

        except json.JSONDecodeError as error:
            print(
                f"[JSON 변환 오류] "
                f"{client_address}: {error}"
            )

            self.send_error_safely(
                client_socket,
                "JSON 형식이 올바르지 않습니다."
            )

        except UnicodeDecodeError as error:
            print(
                f"[UTF-8 변환 오류] "
                f"{client_address}: {error}"
            )

            self.send_error_safely(
                client_socket,
                "문자 인코딩 형식이 올바르지 않습니다."
            )

        except ValueError as error:
            print(
                f"[요청 데이터 오류] "
                f"{client_address}: {error}"
            )

            self.send_error_safely(
                client_socket,
                str(error)
            )

        except OSError as error:
            print(
                f"[소켓 처리 오류] "
                f"{client_address}: {error}"
            )

        except Exception as error:
            print(
                f"[클라이언트 처리 오류] "
                f"{client_address}: {error}"
            )

            self.send_error_safely(
                client_socket,
                "서버에서 요청을 처리하는 중 오류가 발생했습니다."
            )

        finally:
            print(
                f"[클라이언트 연결 종료] "
                f"{client_address}"
            )

    # 예외 처리 중 오류 응답을 안전하게 전송
    def send_error_safely(
        self,
        client_socket,
        message
    ):
        try:
            response = {
                "type": "error",
                "success": False,
                "message": message
            }

            self.send_message(
                client_socket,
                response
            )

        except OSError:
            pass

    # TCP 서버 실행
    def start(self):
        try:
            # TCP 서버 소켓 생성
            self.server_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            # 서버를 재시작할 때 같은 주소와 포트를 빠르게 재사용
            self.server_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            # 서버 주소와 포트 연결
            self.server_socket.bind(
                (
                    self.host,
                    self.port
                )
            )

            # 클라이언트 접속 대기 시작
            self.server_socket.listen()

            # 서버 실행 상태로 변경
            self.running = True

            print("서버를 시작합니다.")
            print(
                f"주소: "
                f"{self.host}:{self.port}"
            )
            print("클라이언트 접속 대기 중...")

            while self.running:
                try:
                    # 새로운 클라이언트 접속 수락
                    client_socket, client_address = (
                        self.server_socket.accept()
                    )

                    # 클라이언트마다 별도의 스레드 생성
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(
                            client_socket,
                            client_address
                        ),
                        daemon=True
                    )

                    thread.start()

                except OSError:
                    # 서버 종료 과정에서 발생한 오류는 무시
                    if not self.running:
                        break

                    raise

        except OSError as error:
            print(
                f"[서버 실행 오류] {error}"
            )

        finally:
            self.stop()

    # 서버 종료
    def stop(self):
        # 서버 실행 상태를 종료로 변경
        self.running = False

        # 서버 소켓이 없다면 종료
        if self.server_socket is None:
            return

        try:
            # 서버 소켓 닫기
            self.server_socket.close()

        except OSError:
            pass

        self.server_socket = None

        print("서버를 종료했습니다.")

if __name__ == "__main__":
    server = Server()
    try:
        server.start()
    # 터미널에서 Ctrl+C를 누른 경우
    except KeyboardInterrupt:
        print("\n서버 종료 요청을 받았습니다.")
    finally:
        server.stop()