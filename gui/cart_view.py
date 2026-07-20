# gui/cart_view.py
# C팀(장바구니/주문처리) 화면 - PySide6
# 화면은 입력/출력만 담당하고, 실제 데이터는 전부 서버(NetworkClient)에서 받아온다.
#
# 구매 버튼을 누르면 여기서 바로 주문을 넣지 않고, order_requested 신호로
# 선택된 항목을 넘겨서 OrderView(주문/결제 확인 화면)로 넘어가게 한다.

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QPushButton, QLabel, QMessageBox,
)


class CartView(QWidget):
    order_requested = Signal(list)  # 주문 화면으로 넘길 cart 항목 목록

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.cart_items = []

        self._build_ui()
        self.load_cart()

    def _build_ui(self):
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        self.total_label = QLabel("총합계: 0원")

        self.btn_delete_all = QPushButton("전체삭제")
        self.btn_delete_select = QPushButton("선택삭제")
        self.btn_order_select = QPushButton("선택구매")
        self.btn_order_all = QPushButton("전체구매")

        self.btn_delete_all.clicked.connect(self.on_delete_all)
        self.btn_delete_select.clicked.connect(self.on_delete_select)
        self.btn_order_select.clicked.connect(self.on_order_select)
        self.btn_order_all.clicked.connect(self.on_order_all)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("[장바구니]"))
        layout.addWidget(self.list_widget)
        layout.addWidget(self.total_label)
        layout.addWidget(self.btn_delete_all)
        layout.addWidget(self.btn_delete_select)
        layout.addWidget(self.btn_order_select)
        layout.addWidget(self.btn_order_all)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    def load_cart(self):
        """서버에서 실제 장바구니 목록을 가져온다."""
        res = self.client.cart_list()
        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "장바구니 조회 실패"))
            return

        self.cart_items = res["data"]
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        for item in self.cart_items:
            text = f'{item["name"]} | {item["price"]:,}원 x {item["quantity"]}개'
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.ItemDataRole.UserRole, item["cart_id"])
            self.list_widget.addItem(list_item)
        self.update_total()

    def update_total(self):
        total = sum(i["price"] * i["quantity"] for i in self.cart_items)
        self.total_label.setText(f"총합계: {total:,}원")

    def on_delete_all(self):
        for item in list(self.cart_items):
            self.client.cart_delete(item["cart_id"])
        self.load_cart()

    def on_delete_select(self):
        for list_item in self.list_widget.selectedItems():
            cart_id = list_item.data(Qt.ItemDataRole.UserRole)
            self.client.cart_delete(cart_id)
        self.load_cart()

    def _selected_rows(self):
        selected_ids = {
            li.data(Qt.ItemDataRole.UserRole) for li in self.list_widget.selectedItems()
        }
        return [row for row in self.cart_items if row["cart_id"] in selected_ids]

    def on_order_all(self):
        if not self.cart_items:
            QMessageBox.information(self, "안내", "장바구니가 비어있습니다.")
            return
        self.order_requested.emit(list(self.cart_items))

    def on_order_select(self):
        selected_rows = self._selected_rows()

        if not selected_rows:
            QMessageBox.information(self, "안내", "주문할 상품을 선택하세요.")
            return

        self.order_requested.emit(selected_rows)
