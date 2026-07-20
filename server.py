# server.py
# A팀(로그인/회원가입) + B팀(상품페이지) + C팀(장바구니/주문) 세 도메인이 합쳐진 서버.
# 다른 팀원(D, E, F)도 자기 도메인 handler를 만들어서
# 아래처럼 import + update()만 추가하면 됨.
#
# 세션 처리: 소켓 연결 하나당 스레드 하나(handle_client)가 붙으므로,
# 그 스레드 지역 변수로 session(dict)을 들고 있으면 "연결 = 로그인 세션"이 된다.
# login이 성공하면 session["member_id"]/session["role"]을 채우고, 그 뒤로는
# 클라이언트가 member_id를 안 보내도 서버가 자동으로 채워서 handler에 넘긴다.

import socket
import threading
import json

from db import get_connection
from handlers.auth_handler import AUTH_ACTION_HANDLERS
from handlers.product_handler import PRODUCT_ACTION_HANDLERS
from handlers.cart_handler import CART_ACTION_HANDLERS
from handlers.board_handler import BOARD_ACTION_HANDLERS

ACTION_HANDLERS = {}
ACTION_HANDLERS.update(AUTH_ACTION_HANDLERS)
ACTION_HANDLERS.update(PRODUCT_ACTION_HANDLERS)
ACTION_HANDLERS.update(CART_ACTION_HANDLERS)
ACTION_HANDLERS.update(BOARD_ACTION_HANDLERS)


# 나중에 추가될 도메인 예시
# from handlers.stats_handler import STATS_ACTION_HANDLERS
# ACTION_HANDLERS.update(STATS_ACTION_HANDLERS)
# from handlers.board_handler import BOARD_ACTION_HANDLERS
# ACTION_HANDLERS.update(BOARD_ACTION_HANDLERS)


def handle_client(conn, addr):
    print(f"[연결됨] {addr}")
    session = {"member_id": None, "role": None}
    buffer = b""
    try:
        while True:
            chunk = conn.recv(1)
            if not chunk:
                break
            if chunk == b"\n":
                request = json.loads(buffer.decode("utf-8"))
                response = process_request(request, session)
                # 수정
                conn.sendall((json.dumps(response, ensure_ascii=False, default=str) + "\n").encode("utf-8"))
                buffer = b""
            else:
                buffer += chunk
    except (ConnectionResetError, json.JSONDecodeError) as e:
        print(f"[오류] {addr} : {e}")
    finally:
        conn.close()
        print(f"[연결 종료] {addr}")


def process_request(request: dict, session: dict) -> dict:
    action = request.get("action")
    handler = ACTION_HANDLERS.get(action)

    if handler is None:
        return {"status": "fail", "message": f"알 수 없는 action: {action}"}

    # 로그인 상태면, 요청에 member_id가 없거나 비어있을 때 세션의 member_id를 자동으로 채워준다.
    if session.get("member_id") is not None and not request.get("member_id"):
        request["member_id"] = session["member_id"]

    # 관리자 전용 액션 가드. 매출통계(stats_*), 재고관리(admin_*) handler가
    # 나중에 ACTION_HANDLERS에 합쳐지면, 이 체크 하나로 권한 없는 접근을 막을 수 있다.
    if (action.startswith("admin_") or action.startswith("stats_")) and session.get("role") != "ADMIN":
        return {"status": "fail", "message": "관리자 권한이 필요합니다."}

    db_conn = get_connection()
    try:
        cursor = db_conn.cursor()
        response = handler(cursor, request)
        db_conn.commit()

        if response.get("status") == "success":
            if action == "login":
                session["member_id"] = response["data"]["member_id"]
                session["role"] = response["data"].get("role")
            elif action in ("logout", "member_withdraw"):
                session["member_id"] = None
                session["role"] = None

        return response
    except Exception as e:
        db_conn.rollback()
        return {"status": "fail", "message": str(e)}
    finally:
        db_conn.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 5000))
    server_socket.listen()
    print(f"서버 시작 (port 5000) - 등록된 action 수: {len(ACTION_HANDLERS)}")
    print(f"게시판 서버 시작 (port 3306) - 등록된 action 수: {len(ACTION_HANDLERS)}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
