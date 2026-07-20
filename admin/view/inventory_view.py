from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QTabWidget,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QMessageBox
)


# 카테고리 추가/수정 다이얼로그
class CategoryDialog(QDialog):
    def __init__(self, parent=None, category=None):
        super().__init__(parent)

        # category가 있으면 수정 모드, 없으면 추가 모드
        self.category = category

        self.setWindowTitle(
            "카테고리 수정" if category else "카테고리 추가"
        )
        self.setMinimumWidth(300)

        self.setup_ui()

        if category is not None:
            self.name_edit.setText(category.get("name", ""))
            self.active_check.setChecked(
                bool(category.get("is_active", True))
            )

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # 카테고리명 입력
        self.name_edit = QLineEdit()
        form_layout.addRow("카테고리명", self.name_edit)

        # 활성 여부 체크박스 (수정 모드에서만 의미가 있음)
        self.active_check = QCheckBox("활성")
        self.active_check.setChecked(True)

        if self.category is None:
            # 추가 시에는 항상 활성 상태로 생성되므로 비활성화해서 표시
            self.active_check.setEnabled(False)

        form_layout.addRow("", self.active_check)

        layout.addLayout(form_layout)

        # 확인/취소 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

    # 입력한 카테고리명 반환
    def get_name(self):
        return self.name_edit.text().strip()

    # 입력한 활성 여부 반환
    def get_is_active(self):
        return self.active_check.isChecked()


# 상품 추가/수정 다이얼로그
class ProductDialog(QDialog):
    def __init__(self, parent=None, categories=None, product=None):
        super().__init__(parent)

        # product가 있으면 수정 모드, 없으면 추가 모드
        self.product = product
        self.categories = categories or []

        self.setWindowTitle(
            "상품 수정" if product else "상품 추가"
        )
        self.setMinimumWidth(360)

        self.setup_ui()

        if product is not None:
            self.fill_product(product)

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # 카테고리 선택
        self.category_combo = QComboBox()
        for category in self.categories:
            self.category_combo.addItem(
                category.get("name", ""),
                category.get("category_id")
            )
        form_layout.addRow("카테고리", self.category_combo)

        # 상품명 입력
        self.name_edit = QLineEdit()
        form_layout.addRow("상품명", self.name_edit)

        # 상품 설명 입력
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(70)
        form_layout.addRow("설명", self.description_edit)

        # 색상 입력
        self.color_edit = QLineEdit()
        form_layout.addRow("색상", self.color_edit)

        # 사이즈 입력
        self.size_edit = QLineEdit()
        form_layout.addRow("사이즈", self.size_edit)

        # 가격 입력
        self.price_spin = QSpinBox()
        self.price_spin.setRange(0, 100_000_000)
        self.price_spin.setSuffix(" 원")
        form_layout.addRow("가격", self.price_spin)

        # 재고수량 입력
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 1_000_000)
        form_layout.addRow("재고수량", self.stock_spin)

        layout.addLayout(form_layout)

        # 확인/취소 버튼
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        self.setLayout(layout)

    # 수정 모드일 때 기존 상품 정보를 입력창에 채움
    def fill_product(self, product):
        self.name_edit.setText(product.get("name", ""))
        self.description_edit.setPlainText(
            product.get("description") or ""
        )
        self.color_edit.setText(product.get("color") or "")
        self.size_edit.setText(product.get("size") or "")
        self.price_spin.setValue(product.get("price") or 0)
        self.stock_spin.setValue(product.get("inventory") or 0)

        category_id = product.get("category_id")
        index = self.category_combo.findData(category_id)

        if index >= 0:
            self.category_combo.setCurrentIndex(index)

    # 입력한 상품 정보를 딕셔너리로 반환
    def get_product_data(self):
        return {
            "category_id": self.category_combo.currentData(),
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "color": self.color_edit.text().strip(),
            "size": self.size_edit.text().strip(),
            "price": self.price_spin.value(),
            "inventory": self.stock_spin.value()
        }


class InventoryWidget(QWidget):
    def __init__(self, client):
        super().__init__()

        # 서버 통신에 사용할 Client 객체 저장
        self.client = client

        # 카테고리 목록 캐시 (상품 다이얼로그의 콤보박스에 사용)
        self.categories = []

        # 재고관리 화면 기본 설정
        self.setWindowTitle("재고관리")
        self.setFixedSize(950, 750)

        # 화면 구성
        self.setup_ui()

        # 서버 응답 Signal 연결
        self.connect_signals()

    # 재고관리 화면 구성
    def setup_ui(self):
        # 전체 화면에서 사용할 세로 레이아웃
        main_layout = QVBoxLayout()

        # 화면 제목
        title_label = QLabel("재고관리")
        main_layout.addWidget(title_label)

        # 카테고리 탭과 상품 탭을 담을 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(
            self.build_category_tab(), "카테고리 관리"
        )
        self.tab_widget.addTab(
            self.build_product_tab(), "상품 관리"
        )

        main_layout.addWidget(self.tab_widget)

        # 현재 위젯에 레이아웃 적용
        self.setLayout(main_layout)

    # 카테고리 관리 탭 구성
    def build_category_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # 상단 버튼 영역
        button_layout = QHBoxLayout()

        self.category_refresh_button = QPushButton("새로고침")
        self.category_add_button = QPushButton("추가")
        self.category_edit_button = QPushButton("수정")

        button_layout.addWidget(self.category_refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.category_add_button)
        button_layout.addWidget(self.category_edit_button)

        layout.addLayout(button_layout)

        # 카테고리 목록 테이블
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(
            ["카테고리ID", "카테고리명", "활성 여부"]
        )
        self.category_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.category_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.category_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.category_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.category_table.doubleClicked.connect(
            self.open_category_edit_dialog
        )

        layout.addWidget(self.category_table)

        tab.setLayout(layout)

        # 버튼 클릭 연결
        self.category_refresh_button.clicked.connect(
            self.request_category_list
        )
        self.category_add_button.clicked.connect(
            self.open_category_add_dialog
        )
        self.category_edit_button.clicked.connect(
            self.open_category_edit_dialog
        )

        return tab

    # 상품 관리 탭 구성
    def build_product_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # 상단 버튼 영역
        button_layout = QHBoxLayout()

        self.product_refresh_button = QPushButton("새로고침")
        self.product_add_button = QPushButton("추가")
        self.product_edit_button = QPushButton("수정")

        button_layout.addWidget(self.product_refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.product_add_button)
        button_layout.addWidget(self.product_edit_button)

        layout.addLayout(button_layout)

        # 상품 목록 테이블
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(8)
        self.product_table.setHorizontalHeaderLabels(
            [
                "상품ID",
                "카테고리",
                "상품명",
                "색상",
                "사이즈",
                "가격",
                "재고",
                "재고 상태"
            ]
        )
        self.product_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.product_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.product_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.product_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.product_table.doubleClicked.connect(
            self.open_product_edit_dialog
        )

        layout.addWidget(self.product_table)

        tab.setLayout(layout)

        # 버튼 클릭 연결
        self.product_refresh_button.clicked.connect(
            self.request_product_list
        )
        self.product_add_button.clicked.connect(
            self.open_product_add_dialog
        )
        self.product_edit_button.clicked.connect(
            self.open_product_edit_dialog
        )

        return tab

    # Client Signal과 응답 처리 메서드 연결
    def connect_signals(self):
        self.client.message_received.connect(
            self.handle_response
        )

        self.client.error_occurred.connect(
            self.handle_error
        )

        self.client.connected.connect(
            self.handle_connected
        )

    # 서버 연결 성공 시 초기 목록 조회
    def handle_connected(self):
        self.request_category_list()
        self.request_product_list()

    # ------------------------------------------------------------
    # 서버 요청
    # ------------------------------------------------------------

    def request_category_list(self):
        self.client.send_message(
            {"type": "category_list"}
        )

    def request_category_add(self, name):
        self.client.send_message(
            {
                "type": "category_add",
                "name": name
            }
        )

    def request_category_update(self, category_id, name, is_active):
        self.client.send_message(
            {
                "type": "category_update",
                "category_id": category_id,
                "name": name,
                "is_active": is_active
            }
        )

    def request_product_list(self):
        self.client.send_message(
            {"type": "inventory_product_list"}
        )

    def request_product_add(self, product_data):
        request = {"type": "product_add"}
        request.update(product_data)

        self.client.send_message(request)

    def request_product_update(self, product_id, product_data):
        request = {
            "type": "product_update",
            "product_id": product_id
        }
        request.update(product_data)

        self.client.send_message(request)

    # ------------------------------------------------------------
    # 카테고리 다이얼로그
    # ------------------------------------------------------------

    def open_category_add_dialog(self):
        dialog = CategoryDialog(self)

        if dialog.exec() != QDialog.Accepted:
            return

        name = dialog.get_name()

        if not name:
            QMessageBox.warning(
                self, "입력 오류", "카테고리명을 입력하세요."
            )
            return

        self.request_category_add(name)

    def open_category_edit_dialog(self):
        row = self.category_table.currentRow()

        if row < 0:
            QMessageBox.information(
                self, "안내", "수정할 카테고리를 선택하세요."
            )
            return

        category_id = int(
            self.category_table.item(row, 0).text()
        )
        current_name = self.category_table.item(row, 1).text()
        current_active = (
            self.category_table.item(row, 2).text() == "활성"
        )

        dialog = CategoryDialog(
            self,
            category={
                "name": current_name,
                "is_active": current_active
            }
        )

        if dialog.exec() != QDialog.Accepted:
            return

        name = dialog.get_name()

        if not name:
            QMessageBox.warning(
                self, "입력 오류", "카테고리명을 입력하세요."
            )
            return

        self.request_category_update(
            category_id,
            name,
            dialog.get_is_active()
        )

    # ------------------------------------------------------------
    # 상품 다이얼로그
    # ------------------------------------------------------------

    def open_product_add_dialog(self):
        if not self.categories:
            QMessageBox.information(
                self,
                "안내",
                "등록된 카테고리가 없습니다. 먼저 카테고리를 추가하세요."
            )
            return

        dialog = ProductDialog(self, categories=self.categories)

        if dialog.exec() != QDialog.Accepted:
            return

        product_data = dialog.get_product_data()

        if not product_data["name"]:
            QMessageBox.warning(
                self, "입력 오류", "상품명을 입력하세요."
            )
            return

        self.request_product_add(product_data)

    def open_product_edit_dialog(self):
        row = self.product_table.currentRow()

        if row < 0:
            QMessageBox.information(
                self, "안내", "수정할 상품을 선택하세요."
            )
            return

        product_id = int(
            self.product_table.item(row, 0).data(Qt.UserRole)
        )
        product = self.product_table.item(row, 0).data(
            Qt.UserRole + 1
        )

        dialog = ProductDialog(
            self,
            categories=self.categories,
            product=product
        )

        if dialog.exec() != QDialog.Accepted:
            return

        product_data = dialog.get_product_data()

        if not product_data["name"]:
            QMessageBox.warning(
                self, "입력 오류", "상품명을 입력하세요."
            )
            return

        self.request_product_update(product_id, product_data)

    # ------------------------------------------------------------
    # 테이블 갱신
    # ------------------------------------------------------------

    def fill_category_table(self, categories):
        self.category_table.setRowCount(len(categories))

        for row, category in enumerate(categories):
            self.category_table.setItem(
                row, 0,
                QTableWidgetItem(str(category.get("category_id", "")))
            )
            self.category_table.setItem(
                row, 1,
                QTableWidgetItem(category.get("name", ""))
            )
            self.category_table.setItem(
                row, 2,
                QTableWidgetItem(
                    "활성" if category.get("is_active") else "비활성"
                )
            )

    def fill_product_table(self, products):
        self.product_table.setRowCount(len(products))

        for row, product in enumerate(products):
            id_item = QTableWidgetItem(
                str(product.get("product_id", ""))
            )

            # 수정 다이얼로그에서 바로 쓸 수 있도록 원본 데이터를 함께 저장
            id_item.setData(Qt.UserRole, product.get("product_id"))
            id_item.setData(Qt.UserRole + 1, product)

            self.product_table.setItem(row, 0, id_item)

            self.product_table.setItem(
                row, 1,
                QTableWidgetItem(product.get("category_name", ""))
            )
            self.product_table.setItem(
                row, 2,
                QTableWidgetItem(product.get("name", ""))
            )
            self.product_table.setItem(
                row, 3,
                QTableWidgetItem(product.get("color") or "")
            )
            self.product_table.setItem(
                row, 4,
                QTableWidgetItem(product.get("size") or "")
            )
            self.product_table.setItem(
                row, 5,
                QTableWidgetItem(str(product.get("price", "")))
            )
            self.product_table.setItem(
                row, 6,
                QTableWidgetItem(str(product.get("inventory", "")))
            )
            self.product_table.setItem(
                row, 7,
                QTableWidgetItem(str(product.get("stock_status", "")))
            )

    # ------------------------------------------------------------
    # 서버 응답 처리
    # ------------------------------------------------------------

    def handle_response(self, response):
        response_type = response.get("type", "")
        success = response.get("success", False)
        message = response.get("message", "")

        if response_type == "category_list":
            if success:
                self.categories = response.get("categories", [])
                self.fill_category_table(self.categories)
            else:
                QMessageBox.warning(self, "카테고리 조회 실패", message)

        elif response_type == "category_add":
            if success:
                QMessageBox.information(self, "카테고리 추가", message)
                self.request_category_list()
            else:
                QMessageBox.warning(self, "카테고리 추가 실패", message)

        elif response_type == "category_update":
            if success:
                QMessageBox.information(self, "카테고리 수정", message)
                self.request_category_list()
            else:
                QMessageBox.warning(self, "카테고리 수정 실패", message)

        elif response_type == "inventory_product_list":
            if success:
                self.fill_product_table(response.get("products", []))
            else:
                QMessageBox.warning(self, "상품 조회 실패", message)

        elif response_type == "product_add":
            if success:
                QMessageBox.information(self, "상품 추가", message)
                self.request_product_list()
            else:
                QMessageBox.warning(self, "상품 추가 실패", message)

        elif response_type == "product_update":
            if success:
                QMessageBox.information(self, "상품 수정", message)
                self.request_product_list()
            else:
                QMessageBox.warning(self, "상품 수정 실패", message)

        elif response_type == "error":
            QMessageBox.warning(self, "요청 오류", message)

        print(
            f"[재고관리 응답] "
            f"{response_type}: {response}"
        )

    # 서버 통신 오류 처리
    def handle_error(self, error_message):
        print(
            f"[재고관리 통신 오류] "
            f"{error_message}"
        )