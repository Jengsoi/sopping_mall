# auth/gui/login_view.py
# 로그인 화면 - PySide6
# client는 login(...) 메서드만 있으면 되므로, AuthNetworkClient 뿐 아니라
# shoppingmall의 NetworkClient에도 그대로 재사용할 수 있다. (동일한 action/파라미터)

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QLabel,
    QFormLayout, QHBoxLayout, QVBoxLayout, QMessageBox,
)

from gui.signup_view import SignupDialog


class LoginView(QWidget):
    login_success = Signal(dict)  # 로그인 성공 시 회원 정보(member_id, login_id, name)를 전달

    def __init__(self, client):
        super().__init__()
        self.client = client
        self._build_ui()

    def _build_ui(self):
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("아이디")

        self.pw_edit = QLineEdit()
        self.pw_edit.setPlaceholderText("비밀번호")
        self.pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_edit.returnPressed.connect(self.on_login)

        form = QFormLayout()
        form.addRow("아이디", self.id_edit)
        form.addRow("비밀번호", self.pw_edit)

        self.btn_login = QPushButton("로그인")
        self.btn_signup = QPushButton("회원가입")
        self.btn_login.clicked.connect(self.on_login)
        self.btn_signup.clicked.connect(self.on_signup)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_login)
        button_layout.addWidget(self.btn_signup)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("[로그인]"))
        layout.addLayout(form)
        layout.addLayout(button_layout)
        layout.addStretch()
        self.setLayout(layout)

    def on_login(self):
        login_id = self.id_edit.text().strip()
        password = self.pw_edit.text()

        if not login_id or not password:
            QMessageBox.warning(self, "안내", "아이디와 비밀번호를 입력하세요.")
            return

        res = self.client.login(login_id, password)
        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "로그인에 실패했습니다."))
            return

        self.pw_edit.clear()
        self.login_success.emit(res["data"])

    def on_signup(self):
        dialog = SignupDialog(self.client, self)
        if dialog.exec():
            QMessageBox.information(self, "안내", "회원가입이 완료되었습니다. 로그인해주세요.")
            self.id_edit.setText(dialog.login_id_edit.text().strip())
            self.pw_edit.setFocus()
