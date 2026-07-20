# board/gui/board_detail_dialog.py
# 게시글 상세보기 + 댓글 다이얼로그 - PySide6

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QLabel, QTextEdit, QListWidget, QListWidgetItem, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QInputDialog,
)

from gui.board_write_dialog import BoardWriteDialog


class BoardDetailDialog(QDialog):
    def __init__(self, client, post_id, parent=None):
        super().__init__(parent)
        self.client = client
        self.post_id = post_id
        self.post = None

        self.setWindowTitle("게시글 보기")
        self.resize(520, 600)

        self._build_ui()
        self.load_post()

    def _build_ui(self):
        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.meta_label = QLabel("")

        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)

        self.edit_button = QPushButton("수정")
        self.delete_button = QPushButton("삭제")
        self.edit_button.clicked.connect(self.edit_post)
        self.delete_button.clicked.connect(self.delete_post)

        post_button_layout = QHBoxLayout()
        post_button_layout.addStretch()
        post_button_layout.addWidget(self.edit_button)
        post_button_layout.addWidget(self.delete_button)

        self.comment_list = QListWidget()

        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("댓글을 입력하세요...")
        self.comment_edit.setFixedHeight(60)

        add_comment_button = QPushButton("댓글 등록")
        add_comment_button.clicked.connect(self.add_comment)

        edit_comment_button = QPushButton("댓글 수정")
        delete_comment_button = QPushButton("댓글 삭제")
        edit_comment_button.clicked.connect(self.edit_comment)
        delete_comment_button.clicked.connect(self.delete_comment)

        comment_button_layout = QHBoxLayout()
        comment_button_layout.addWidget(add_comment_button)
        comment_button_layout.addStretch()
        comment_button_layout.addWidget(edit_comment_button)
        comment_button_layout.addWidget(delete_comment_button)

        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.content_view)
        layout.addLayout(post_button_layout)
        layout.addWidget(QLabel("댓글"))
        layout.addWidget(self.comment_list)
        layout.addWidget(self.comment_edit)
        layout.addLayout(comment_button_layout)
        layout.addWidget(close_button)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    def load_post(self):
        res = self.client.board_detail(self.post_id)
        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "게시글 조회 실패"))
            self.reject()
            return

        self.post = res["data"]
        self.title_label.setText(self.post["title"])
        self.meta_label.setText(f'작성자: {self.post.get("author") or "-"}  |  작성일: {self.post["created_at"]}')
        self.content_view.setPlainText(self.post.get("content") or "")

        self.comment_list.clear()
        for c in self.post.get("comments", []):
            text = f'{c.get("author") or "-"} : {c["content"]}  ({c["created_at"]})'
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, c["comment_id"])
            self.comment_list.addItem(item)

    def edit_post(self):
        dialog = BoardWriteDialog(self.client, self, post=self.post)
        if dialog.exec():
            self.load_post()

    def delete_post(self):
        confirm = QMessageBox.question(self, "삭제 확인", "게시글을 삭제하시겠습니까?")
        if confirm != QMessageBox.StandardButton.Yes:
            return

        res = self.client.board_delete(self.post_id)
        if res.get("status") == "success":
            self.accept()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "삭제에 실패했습니다."))

    def add_comment(self):
        content = self.comment_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "안내", "댓글 내용을 입력하세요.")
            return

        res = self.client.comment_create(self.post_id, content)
        if res.get("status") == "success":
            self.comment_edit.clear()
            self.load_post()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "댓글 등록에 실패했습니다."))

    def get_selected_comment_id(self):
        item = self.comment_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def edit_comment(self):
        comment_id = self.get_selected_comment_id()
        if comment_id is None:
            QMessageBox.information(self, "안내", "수정할 댓글을 선택하세요.")
            return

        comment = next((c for c in self.post["comments"] if c["comment_id"] == comment_id), None)
        current_text = comment["content"] if comment else ""

        text, ok = QInputDialog.getMultiLineText(self, "댓글 수정", "내용", current_text)
        if not ok:
            return

        text = text.strip()
        if not text:
            QMessageBox.warning(self, "안내", "댓글 내용을 입력하세요.")
            return

        res = self.client.comment_update(comment_id, text)
        if res.get("status") == "success":
            self.load_post()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "댓글 수정에 실패했습니다."))

    def delete_comment(self):
        comment_id = self.get_selected_comment_id()
        if comment_id is None:
            QMessageBox.information(self, "안내", "삭제할 댓글을 선택하세요.")
            return

        confirm = QMessageBox.question(self, "삭제 확인", "댓글을 삭제하시겠습니까?")
        if confirm != QMessageBox.StandardButton.Yes:
            return

        res = self.client.comment_delete(comment_id)
        if res.get("status") == "success":
            self.load_post()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "댓글 삭제에 실패했습니다."))
