# network_client.py
# 6개 도메인(A~F)이 공통으로 사용하는 클라이언트 통신 클래스
#
# 요청 형식: {"action": "...", ...데이터...}
# 응답 형식: {"status": "success" | "fail", "data": {...} 또는 "message": "..."}
#
# 메시지 경계는 줄바꿈(\n)으로 구분한다.
# (JSON 문자열 안에는 실제 줄바꿈이 올 수 없으므로 구분자로 안전하게 사용 가능)

import socket
import json


class NetworkClient:
    def __init__(self, host="localhost", port=5000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    # ---------------------------------------------------------
    # 내부 통신 처리 (다른 팀원은 이 두 메서드를 직접 건드릴 필요 없음)
    # ---------------------------------------------------------
    def _send(self, payload: dict) -> dict:
        message = json.dumps(payload, ensure_ascii=False) + "\n"
        self.sock.sendall(message.encode("utf-8"))
        return self._recv_json()

    def _recv_json(self) -> dict:
        buffer = b""
        while True:
            chunk = self.sock.recv(1)
            if not chunk or chunk == b"\n":
                break
            buffer += chunk
        return json.loads(buffer.decode("utf-8"))

    def close(self):
        self.sock.close()

    # ===========================================================
    # A. 회원가입 / 로그인
    # ===========================================================
    def signup(self, login_id, password, name, address="", email="", phone="", gender=""):
        return self._send({
            "action": "signup",
            "login_id": login_id,
            "password": password,
            "name": name,
            "address": address,
            "email": email,
            "phone": phone,
            "gender": gender,
        })

    def check_id(self, login_id):
        return self._send({
            "action": "check_id",
            "login_id": login_id,
        })

    def login(self, login_id, password):
        return self._send({
            "action": "login",
            "login_id": login_id,
            "password": password,
        })

    def logout(self):
        return self._send({
            "action": "logout",
        })

    def member_info(self, member_id=None):
        return self._send({
            "action": "member_info",
            "member_id": member_id,   # None이면 서버가 로그인한 본인 정보로 처리
        })

    def member_update(self, name=None, address=None, email=None, phone=None, gender=None):
        return self._send({
            "action": "member_update",
            "name": name,
            "address": address,
            "email": email,
            "phone": phone,
            "gender": gender,
        })

    def member_withdraw(self):
        return self._send({
            "action": "member_withdraw",
        })

    # ===========================================================
    # B. 상품페이지
    # ===========================================================
    def category_list(self):
        return self._send({
            "action": "category_list",
        })

    def product_list(self, category_id=None, keyword=""):
        return self._send({
            "action": "product_list",
            "category_id": category_id,
            "keyword": keyword,
        })

    def product_detail(self, product_id):
        return self._send({
            "action": "product_detail",
            "product_id": product_id,
        })

    # ===========================================================
    # C. 장바구니 / 주문처리
    # ===========================================================
    def cart_list(self):
        return self._send({
            "action": "cart_list",
        })

    def cart_add(self, product_id, quantity=1):
        return self._send({
            "action": "cart_add",
            "product_id": product_id,
            "quantity": quantity,
        })

    def cart_update(self, cart_id, quantity):
        return self._send({
            "action": "cart_update",
            "cart_id": cart_id,
            "quantity": quantity,
        })

    def cart_delete(self, cart_id):
        return self._send({
            "action": "cart_delete",
            "cart_id": cart_id,
        })

    def order_create(self, order_items):
        # order_items 예시: [{"product_id": 7, "quantity": 2}, {"product_id": 12, "quantity": 1}]
        # 전체 주문이면 장바구니 전체를, 선택 주문이면 체크된 항목만 리스트로 담아서 전달
        return self._send({
            "action": "order_create",
            "order_items": order_items,
        })

    def order_list(self):
        return self._send({
            "action": "order_list",
        })

    def order_detail(self, order_id):
        return self._send({
            "action": "order_detail",
            "order_id": order_id,
        })

    # ===========================================================
    # D. 매출통계 (관리자)
    # ===========================================================
    def stats_sales_daily(self, start_date, end_date):
        return self._send({
            "action": "stats_sales_daily",
            "start_date": start_date,
            "end_date": end_date,
        })

    def stats_sales_monthly(self, year):
        return self._send({
            "action": "stats_sales_monthly",
            "year": year,
        })

    def stats_best_products(self, start_date, end_date, limit=10):
        return self._send({
            "action": "stats_best_products",
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        })

    def stats_sales_by_category(self, start_date, end_date):
        return self._send({
            "action": "stats_sales_by_category",
            "start_date": start_date,
            "end_date": end_date,
        })

    # ===========================================================
    # E. 데이터(회원/상품) 관리 (관리자)
    # ===========================================================
    def admin_member_list(self, keyword="", page=1, size=20):
        return self._send({
            "action": "admin_member_list",
            "keyword": keyword,
            "page": page,
            "size": size,
        })

    def admin_member_status_update(self, member_id, is_active):
        return self._send({
            "action": "admin_member_status_update",
            "member_id": member_id,
            "is_active": is_active,
        })

    def admin_category_create(self, name):
        return self._send({
            "action": "admin_category_create",
            "name": name,
        })

    def admin_category_update(self, category_id, name=None, is_active=None):
        return self._send({
            "action": "admin_category_update",
            "category_id": category_id,
            "name": name,
            "is_active": is_active,
        })

    def admin_product_create(self, category_id, name, price, description="", color="", size="", stock=0):
        return self._send({
            "action": "admin_product_create",
            "category_id": category_id,
            "name": name,
            "description": description,
            "color": color,
            "size": size,
            "price": price,
            "stock": stock,
        })

    def admin_product_update(self, product_id, name=None, description=None, color=None,
                              size=None, price=None, stock=None, is_active=None):
        return self._send({
            "action": "admin_product_update",
            "product_id": product_id,
            "name": name,
            "description": description,
            "color": color,
            "size": size,
            "price": price,
            "stock": stock,
            "is_active": is_active,
        })

    def admin_product_delete(self, product_id):
        return self._send({
            "action": "admin_product_delete",
            "product_id": product_id,
        })

    # ===========================================================
    # F. 게시판 관리
    # ===========================================================
    def board_list(self, page=1, size=20, keyword=""):
        return self._send({
            "action": "board_list",
            "page": page,
            "size": size,
            "keyword": keyword,
        })

    def board_detail(self, post_id):
        return self._send({
            "action": "board_detail",
            "post_id": post_id,
        })

    def board_create(self, title, content=""):
        return self._send({
            "action": "board_create",
            "title": title,
            "content": content,
        })

    def board_update(self, post_id, title=None, content=None):
        return self._send({
            "action": "board_update",
            "post_id": post_id,
            "title": title,
            "content": content,
        })

    def board_delete(self, post_id):
        return self._send({
            "action": "board_delete",
            "post_id": post_id,
        })

    def comment_create(self, post_id, content):
        return self._send({
            "action": "comment_create",
            "post_id": post_id,
            "content": content,
        })

    def comment_update(self, comment_id, content):
        return self._send({
            "action": "comment_update",
            "comment_id": comment_id,
            "content": content,
        })

    def comment_delete(self, comment_id):
        return self._send({
            "action": "comment_delete",
            "comment_id": comment_id,
        })

