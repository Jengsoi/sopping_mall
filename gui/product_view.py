# gui/product_view.py
# B팀(상품페이지) 화면 - PySide6
# 화면은 입력/출력만 담당하고, 실제 데이터는 전부 서버(NetworkClient)에서 받아온다.

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QSpinBox, QVBoxLayout, QHBoxLayout, QMessageBox,
)


class ProductView(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.categories = []
        self.selected_product_id = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.search)

        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("상품명 검색...")
        self.keyword_edit.returnPressed.connect(self.search)

        search_button = QPushButton("검색")
        search_button.clicked.connect(self.search)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("카테고리"))
        search_layout.addWidget(self.category_combo)
        search_layout.addWidget(self.keyword_edit)
        search_layout.addWidget(search_button)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["상품명", "색상", "사이즈", "가격", "재고"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.show_detail)
        self.table.setColumnWidth(0, 240)

        self.detail_label = QLabel("상품을 선택하면 상세 정보가 표시됩니다.")
        self.detail_label.setWordWrap(True)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999)

        self.add_cart_button = QPushButton("장바구니 담기")
        self.add_cart_button.setEnabled(False)
        self.add_cart_button.clicked.connect(self.add_to_cart)

        cart_layout = QHBoxLayout()
        cart_layout.addWidget(QLabel("수량"))
        cart_layout.addWidget(self.quantity_spin)
        cart_layout.addWidget(self.add_cart_button)
        cart_layout.addStretch()

        self.message_label = QLabel("")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("[상품페이지]"))
        layout.addLayout(search_layout)
        layout.addWidget(self.table)
        layout.addWidget(QLabel("상품 정보"))
        layout.addWidget(self.detail_label)
        layout.addLayout(cart_layout)
        layout.addWidget(self.message_label)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    def refresh(self):
        """카테고리 목록을 다시 불러오고 상품 목록도 갱신한다."""
        res = self.client.category_list()

        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("전체", None)

        if res.get("status") == "success":
            self.categories = res["data"]
            for c in self.categories:
                self.category_combo.addItem(c["name"], c["category_id"])
        else:
            QMessageBox.warning(self, "오류", res.get("message", "카테고리 조회 실패"))

        self.category_combo.blockSignals(False)
        self.load_products()

    def search(self):
        self.load_products()

    def load_products(self):
        category_id = self.category_combo.currentData()
        keyword = self.keyword_edit.text().strip()

        res = self.client.product_list(category_id=category_id, keyword=keyword)
        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "상품 조회 실패"))
            return

        products = res["data"]
        self.table.setRowCount(len(products))

        for row, p in enumerate(products):
            name_item = QTableWidgetItem(p["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, p["product_id"])

            stock_text = "품절" if p["stock"] == 0 else str(p["stock"])

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(p.get("color") or "-"))
            self.table.setItem(row, 2, QTableWidgetItem(p.get("size") or "-"))
            self.table.setItem(row, 3, QTableWidgetItem(f'{p["price"]:,}원'))
            self.table.setItem(row, 4, QTableWidgetItem(stock_text))

        self.detail_label.setText("상품을 선택하면 상세 정보가 표시됩니다.")
        self.add_cart_button.setEnabled(False)
        self.selected_product_id = None

    def get_selected_product_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def show_detail(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            return

        res = self.client.product_detail(product_id)
        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "상세 조회 실패"))
            return

        p = res["data"]
        self.selected_product_id = p["product_id"]

        option_text = " / ".join(filter(None, [p.get("color"), p.get("size")]))
        stock_text = "품절" if p["stock"] == 0 else f'{p["stock"]}개'
        title = f'{p["name"]} ({option_text})' if option_text else p["name"]

        self.detail_label.setText(
            f'{title} | {p["price"]:,}원 | 재고 {stock_text}\n{p.get("description") or ""}'
        )
        self.add_cart_button.setEnabled(p["stock"] > 0)

    def add_to_cart(self):
        if self.selected_product_id is None:
            self.message_label.setText("먼저 상품을 선택하세요.")
            return

        quantity = self.quantity_spin.value()
        res = self.client.cart_add(self.selected_product_id, quantity)

        if res.get("status") == "success":
            self.message_label.setText("장바구니에 담았습니다.")
        else:
            self.message_label.setText(res.get("message", "담기에 실패했습니다."))
