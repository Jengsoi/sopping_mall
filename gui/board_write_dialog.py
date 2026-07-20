# board/gui/board_write_dialog.py
# 게시글 작성/수정 다이얼로그 - PySide6
# post 인자가 주어지면 수정 모드로 동작한다.

from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox,
)


class BoardWriteDialog(QDialog):
    def __init__(self, client, parent=None, post=None):
        super().__init__(parent)
        self.client = client
        self.post = post

        self.setWindowTitle("게시글 수정" if post else "게시글 작성")
        self.resize(480, 400)

        self._build_ui()

        if post:
            self.title_edit.setText(post["title"])
            self.content_edit.setPlainText(post.get("content") or "")

    def _build_ui(self):
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("제목")

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("내용")

        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        save_button.clicked.connect(self.save)
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("제목"))
        layout.addWidget(self.title_edit)
        layout.addWidget(QLabel("내용"))
        layout.addWidget(self.content_edit)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save(self):
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText()

        if not title:
            QMessageBox.warning(self, "안내", "제목을 입력하세요.")
            return

        if self.post:
            res = self.client.board_update(self.post["post_id"], title=title, content=content)
        else:
            res = self.client.board_create(title, content)

        if res.get("status") == "success":
            self.accept()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "저장에 실패했습니다."))
