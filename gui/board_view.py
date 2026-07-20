# board/gui/board_view.py
# F팀(게시판 관리) 메인 화면 - PySide6
# 화면은 입력/출력만 담당하고, 실제 데이터는 전부 서버(BoardNetworkClient)에서 받아온다.

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QMessageBox,
)

from gui.board_write_dialog import BoardWriteDialog
from gui.board_detail_dialog import BoardDetailDialog


class BoardView(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.posts = []
        self.page = 1
        self.size = 20
        self.total = 0

        self._build_ui()
        self.load_posts()

    def _build_ui(self):
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("제목 검색...")
        self.keyword_edit.returnPressed.connect(self.search)

        search_button = QPushButton("검색")
        search_button.clicked.connect(self.search)

        write_button = QPushButton("글쓰기")
        write_button.clicked.connect(self.open_write_dialog)

        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.load_posts)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("[게시판]"))
        top_layout.addStretch()
        top_layout.addWidget(self.keyword_edit)
        top_layout.addWidget(search_button)
        top_layout.addWidget(write_button)
        top_layout.addWidget(refresh_button)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["제목", "작성자", "작성일", "댓글"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setColumnWidth(0, 320)
        self.table.itemDoubleClicked.connect(self.open_selected_detail)

        self.prev_button = QPushButton("이전")
        self.next_button = QPushButton("다음")
        self.page_label = QLabel("1 페이지")
        self.prev_button.clicked.connect(self.go_prev_page)
        self.next_button.clicked.connect(self.go_next_page)

        page_layout = QHBoxLayout()
        page_layout.addStretch()
        page_layout.addWidget(self.prev_button)
        page_layout.addWidget(self.page_label)
        page_layout.addWidget(self.next_button)
        page_layout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.table)
        layout.addLayout(page_layout)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    def search(self):
        self.page = 1
        self.load_posts()

    def load_posts(self):
        keyword = self.keyword_edit.text().strip()
        res = self.client.board_list(page=self.page, size=self.size, keyword=keyword)

        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "게시글 조회 실패"))
            return

        data = res["data"]
        self.posts = data["posts"]
        self.total = data["total"]

        self.table.setRowCount(len(self.posts))
        for row, p in enumerate(self.posts):
            title_item = QTableWidgetItem(p["title"])
            title_item.setData(Qt.ItemDataRole.UserRole, p["post_id"])

            self.table.setItem(row, 0, title_item)
            self.table.setItem(row, 1, QTableWidgetItem(p.get("author") or "-"))
            self.table.setItem(row, 2, QTableWidgetItem(str(p["created_at"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(p.get("comment_count", 0))))

        last_page = max(1, (self.total + self.size - 1) // self.size)
        self.page_label.setText(f"{self.page} / {last_page} 페이지 (전체 {self.total}건)")
        self.prev_button.setEnabled(self.page > 1)
        self.next_button.setEnabled(self.page < last_page)

    def go_prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load_posts()

    def go_next_page(self):
        self.page += 1
        self.load_posts()

    def open_write_dialog(self):
        dialog = BoardWriteDialog(self.client, self)
        if dialog.exec():
            self.load_posts()

    def open_selected_detail(self, item):
        post_id = self.table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.open_detail(post_id)

    def open_detail(self, post_id):
        dialog = BoardDetailDialog(self.client, post_id, self)
        dialog.exec()
        self.load_posts()
