# 바뀐 부분:
#   1) logout_requested 시그널 추가 (소비자 main.py의 on_logout과 동일한 방식으로 연결하기 위함)
#   2) 우측 상단에 "로그아웃" 버튼 추가 -> 누르면 logout_requested emit
#   3) 아래쪽 if __name__ == "__main__" 은 그대로 둠 (단독 실행 테스트용, import 시엔 실행 안 됨)

import sys
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QMessageBox, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel
)

from admin.client.inventory_client import Client
from admin.view.inventory_view import InventoryWidget
from admin.view.dashboard_view import DashboardView


class MainApplication(QWidget):
    logout_requested = Signal()  # 소비자 화면으로 돌아가기 (로그아웃)

    def __init__(self):
        super().__init__()

        # 메인 윈도우 기본 설정
        self.setWindowTitle("통합 매장 관리 시스템")
        self.resize(950, 750)

        # 1. 전체 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1-1. 상단 바 (관리자 표시 + 로그아웃 버튼)
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("관리자 모드"))
        top_bar.addStretch()
        self.btn_logout = QPushButton("로그아웃")
        self.btn_logout.clicked.connect(self.logout_requested)
        top_bar.addWidget(self.btn_logout)
        main_layout.addLayout(top_bar)

        # 2. QTabWidget 생성 및 레이아웃에 추가
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 3. 재고관리용 네트워크 클라이언트 생성 및 연결 시작
        self.inventory_client = Client()
        self.inventory_client.error_occurred.connect(self.handle_inventory_error)


        # 4. 각각의 화면(Widget) 인스턴스 생성
        # 대시보드 화면 (내부에서 NetworkClient를 통해 6001 포트로 자동 연결됨)
        self.dashboard_view = DashboardView()
        # 재고관리 화면 (생성한 클라이언트 객체를 주입)
        self.inventory_widget = InventoryWidget(self.inventory_client)

        # 5. QTabWidget에 탭으로 추가
        self.tab_widget.addTab(self.dashboard_view, "📊 매출 현황 (대시보드)")
        self.tab_widget.addTab(self.inventory_widget, "📦 재고 관리")

        self.inventory_client.connect_server()

    def handle_inventory_error(self, error_message):
        """재고관리 서버 연결 실패 시 알림창 표시"""
        QMessageBox.warning(
            self,
            "서버 연결 알림 (재고관리)",
            f"재고관리 서버 상태를 확인해 주세요.\n오류 내용: {error_message}"
        )

    def closeEvent(self, event):
        """프로그램이 종료될 때 네트워크 연결을 안전하게 닫음"""
        # 재고관리 클라이언트 소켓 닫기
        if self.inventory_client:
            self.inventory_client.disconnect_server()

        # 대시보드 클라이언트 소켓 닫기 (NetworkClient에 종료 로직이 따로 없으므로 소켓 직접 해제)
        try:
            if hasattr(self.dashboard_view, 'client') and self.dashboard_view.client:
                if self.dashboard_view.client.sock:
                    self.dashboard_view.client.sock.close()
        except Exception as e:
            print(f"대시보드 클라이언트 종료 중 예외 발생: {e}")

        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()