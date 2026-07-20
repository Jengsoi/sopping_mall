# admin_main.py
# A팀(로그인/회원가입) + B팀(상품페이지) + C팀(장바구니/주문) 통합 실행 파일
#
# 실행 전 준비:
#   1) db.py 의 MySQL 접속 정보 수정 (서버 실행 컴퓨터에서만 필요)
#   2) 터미널 1: python server.py
#   3) 터미널 2: python admin_main.py
#
# 화면 전환 구조:
#   최상위 QStackedWidget
#     [0] LoginView (로그인/회원가입)                 <- 앱 시작 시 항상 여기
#     [1] MainWindow 또는 MainApplication(관리자) (로그인 성공 후)  <- role에 따라 분기
#
#   MainWindow 내부 QStackedWidget (기존 그대로)
#     [0] QTabWidget (상품페이지 + 장바구니 + 내 정보)
#     [1] OrderView (주문/결제 확인 화면)
#
# --- 변경 사항 (관리자 연동) ---
#   1) admin_main.py 에서 MainApplication import 추가
#   2) on_login_success(member) 안에서 member["role"] 값을 보고 분기
#      - server.py 의 handlers/auth_handler.py 가 로그인 성공 시
#        response["data"] 안에 "role" 키(예: "ADMIN" / 그 외)를 담아 보내준다는 전제.
#        실제로 그렇게 오는지는 로그인 후 print(member) 로 직접 찍어서 꼭 확인할 것.
#      - server.py 의 process_request() 는 이미 session["role"] != "ADMIN" 이면
#        admin_*/stats_* action을 막고 있으므로, 서버 쪽 권한 체크는 이미 되어 있는 상태.
#        여기서는 "화면 전환"만 담당한다.
#   3) MainApplication 에도 logout_requested 시그널을 추가해서 기존 on_logout 로직을 그대로 재사용.
#
# --- 주의 (확인 필요) ---
#   - 관리자 프로그램이 접속하는 inventory_server(6000)/dashboard_server(6001)는
#     지금 이 member.role 검증과 별개로 동작한다 (자체 인증이 사실상 없음).
#     즉 여기서 막는 건 "이 앱 화면에서 관리자 탭으로 들어가는 것"까지이고,
#     6000/6001 포트 자체의 보안은 별도로 다뤄야 하는 문제다.

import sys
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QWidget, QTabWidget, QStackedWidget, QVBoxLayout

from network_client import NetworkClient
from gui.product_view import ProductView
from gui.cart_view import CartView
from gui.order_view import OrderView
from gui.login_view import LoginView
from gui.member_view import MemberView
from gui.board_view import BoardView
from admin.admin_main import MainApplication

class MainWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, client, member):
        super().__init__()
        self.setWindowTitle("쇼핑몰")
        self.resize(950, 750)

        self.product_view = ProductView(client)
        self.cart_view = CartView(client)
        self.order_view = OrderView(client)
        self.member_view = MemberView(client, member)
        self.member_view.logout_requested.connect(self.logout_requested)
        self.board_view = BoardView(client)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.product_view, "상품페이지")
        self.tabs.addTab(self.cart_view, "장바구니")
        self.tabs.addTab(self.member_view, "내 정보")
        self.tabs.addTab(self.board_view, "게시판")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.tabs)        # index 0: 메인 화면
        self.stack.addWidget(self.order_view)  # index 1: 주문/결제 화면

        # 장바구니 -> 주문화면 전환
        self.cart_view.order_requested.connect(self._show_order_page)
        # 주문화면 -> 메인 화면 복귀 (결제 성공/뒤로가기 둘 다)
        self.order_view.order_completed.connect(self._back_to_main)
        self.order_view.order_cancelled.connect(self._back_to_main)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def _on_tab_changed(self, index):
        # 장바구니 탭으로 전환될 때마다 최신 데이터로 자동 갱신
        if self.tabs.widget(index) is self.cart_view:
            self.cart_view.load_cart()

    def _show_order_page(self, order_items):
        self.order_view.set_items(order_items)
        self.stack.setCurrentWidget(self.order_view)

    def _back_to_main(self):
        self.cart_view.load_cart()          # 결제로 빠진 상품 반영해서 다시 불러오기
        self.stack.setCurrentWidget(self.tabs)
        self.tabs.setCurrentWidget(self.cart_view)


def main():
    app = QApplication(sys.argv)

    client = NetworkClient(host="localhost", port=5000)

    root_stack = QStackedWidget()
    root_stack.setWindowTitle("쇼핑몰")
    root_stack.resize(950, 750)

    login_view = LoginView(client)
    root_stack.addWidget(login_view)  # index 0: 로그인/회원가입

    def on_login_success(member):
        # member: login_view.py 가 emit 하는 dict (res["data"])
        # auth_handler.py 의 login 처리 결과에 "role" 키가 있어야 여기서 분기 가능하다.
        # 직접 실행해서 print(member) 로 실제로 role 값이 오는지 반드시 확인할 것.
        is_admin = member.get("role") == "ADMIN"

        if is_admin:
            view = MainApplication()
        else:
            view = MainWindow(client, member)

        view.logout_requested.connect(on_logout)
        root_stack.addWidget(view)
        root_stack.setCurrentWidget(view)

    def on_logout():
        current = root_stack.currentWidget()
        root_stack.resize(950, 750)
        root_stack.setCurrentWidget(login_view)
        root_stack.removeWidget(current)
        current.deleteLater()

    login_view.login_success.connect(on_login_success)

    root_stack.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()