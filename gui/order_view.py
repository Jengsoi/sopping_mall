# gui/order_view.py
# 장바구니 -> 여기로 넘어와서 최종 확인 후 결제하는 화면.
# 실제 order_create 호출은 여기(결제하기 버튼)에서 일어난다.

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QLabel, QPushButton, QVBoxLayout, QMessageBox,
)

class OrderView(QWidget):
    order_completed = Signal()   # 결제 성공 -> 메인 화면으로 복귀
    order_cancelled = Signal()   # 뒤로가기 -> 메인 화면으로 복귀 (주문 안 함)

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.order_items = []

        self._build_ui()

    def _build_ui(self):
        self.list_widget = QListWidget()
        self.total_label = QLabel("결제 금액: 0원")

        self.id_label = QLabel("")
        self.num_label = QLabel("")
        self.addr_label = QLabel("")

        self.btn_back = QPushButton("뒤로가기")
        self.btn_pay = QPushButton("결제하기")

        self.btn_back.clicked.connect(self.on_back)
        self.btn_pay.clicked.connect(self.on_pay)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("[주문/결제]"))
        layout.addWidget(self.list_widget)
        layout.addWidget(self.id_label)
        layout.addWidget(self.num_label)
        layout.addWidget(self.addr_label)

        layout.addWidget(self.total_label)
        layout.addWidget(self.btn_back)
        layout.addWidget(self.btn_pay)
        self.setLayout(layout)

    def set_items(self, order_items):
        """장바구니 화면에서 넘어온 주문 대상 항목을 표시한다."""
        self.order_items = order_items
        self.refresh_list()

    def set_items(self, order_items):
        """장바구니 화면에서 넘어온 주문 대상 항목을 표시한다."""
        self.order_items = order_items
        self.refresh_list()
        self.load_member_info()  # ← 이 줄 추가: 주문화면 들어올 때마다 최신 정보로 갱신

    def load_member_info(self):  # ← 메서드 새로 추가
        res = self.client.member_info()
        if res.get("status") == "success":
            info = res["data"]
            self.id_label.setText(f'이름: {info.get("name") or "-"}')
            self.num_label.setText(f'전화번호: {info.get("phone") or "미등록"}')
            self.addr_label.setText(f'주소: {info.get("address") or "미등록"}')
        else:
            self.id_label.setText("이름: -")
            self.num_label.setText("전화번호: -")
            self.addr_label.setText("주소: -")

    def refresh_list(self):
        self.list_widget.clear()
        for item in self.order_items:
            text = f'{item["name"]} | {item["price"]:,}원 x {item["quantity"]}개'
            self.list_widget.addItem(QListWidgetItem(text))
        self.update_total()

    def update_total(self):
        total = sum(i["price"] * i["quantity"] for i in self.order_items)
        self.total_label.setText(f"결제 금액: {total:,}원")

    def on_back(self):
        self.order_cancelled.emit()

    def on_pay(self):
        if not self.order_items:
            QMessageBox.information(self, "안내", "주문할 상품이 없습니다.")
            return

        # 서버에는 필요한 것만 보낸다 (name/price는 서버가 최신값으로 다시 조회함)
        order_items = [
            {"cart_id": item["cart_id"], "product_id": item["product_id"], "quantity": item["quantity"]}
            for item in self.order_items
        ]

        res = self.client.order_create(order_items)

        if res.get("status") == "success":
            order_id = res["data"]["order_id"]
            QMessageBox.information(self, "완료", f"주문이 완료되었습니다. (주문번호 {order_id})")
            self.order_items = []
            self.order_completed.emit()
        else:
            QMessageBox.warning(self, "실패", res.get("message", "주문에 실패했습니다."))
