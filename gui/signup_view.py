# auth/gui/signup_view.py
# 회원가입 다이얼로그 - PySide6
# client는 signup(...) / check_id(...) 메서드만 있으면 되므로,
# AuthNetworkClient 뿐 아니라 shoppingmall의 NetworkClient에도 그대로 재사용할 수 있다.

from PySide6.QtWidgets import (
    QDialog, QLineEdit, QComboBox, QPushButton, QLabel,
    QFormLayout, QHBoxLayout, QVBoxLayout, QMessageBox,
)


class SignupDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._id_checked = False

        self.setWindowTitle("회원가입")
        self.resize(950, 750)
        self._build_ui()

    def _build_ui(self):
        self.login_id_edit = QLineEdit()
        self.login_id_edit.setPlaceholderText("아이디")
        self.login_id_edit.textChanged.connect(self._on_id_changed)

        self.btn_check_id = QPushButton("중복확인")
        self.btn_check_id.clicked.connect(self.on_check_id)

        id_row = QHBoxLayout()
        id_row.addWidget(self.login_id_edit)
        id_row.addWidget(self.btn_check_id)

        self.pw_edit = QLineEdit()
        self.pw_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.pw_confirm_edit = QLineEdit()
        self.pw_confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()

        self.gender_combo = QComboBox()
        self.gender_combo.addItem("선택 안 함", "")
        self.gender_combo.addItem("남성", "M")
        self.gender_combo.addItem("여성", "F")

        form = QFormLayout()
        form.addRow("아이디", id_row)
        form.addRow("비밀번호", self.pw_edit)
        form.addRow("비밀번호 확인", self.pw_confirm_edit)
        form.addRow("이름", self.name_edit)
        form.addRow("주소", self.address_edit)
        form.addRow("이메일", self.email_edit)
        form.addRow("전화번호", self.phone_edit)
        form.addRow("성별", self.gender_combo)

        btn_save = QPushButton("가입하기")
        btn_cancel = QPushButton("취소")
        btn_save.clicked.connect(self.on_signup)
        btn_cancel.clicked.connect(self.reject)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(btn_save)
        button_row.addWidget(btn_cancel)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("[회원가입]"))
        layout.addLayout(form)
        layout.addLayout(button_row)
        self.setLayout(layout)

    def _on_id_changed(self):
        self._id_checked = False  # 아이디를 바꾸면 다시 중복확인 필요

    def on_check_id(self):
        login_id = self.login_id_edit.text().strip()
        if not login_id:
            QMessageBox.warning(self, "안내", "아이디를 입력하세요.")
            return

        res = self.client.check_id(login_id)
        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "중복확인에 실패했습니다."))
            return

        if res["data"]["available"]:
            self._id_checked = True
            QMessageBox.information(self, "안내", "사용 가능한 아이디입니다.")
        else:
            self._id_checked = False
            QMessageBox.warning(self, "안내", "이미 사용 중인 아이디입니다.")

    def on_signup(self):
        login_id = self.login_id_edit.text().strip()
        password = self.pw_edit.text()
        password_confirm = self.pw_confirm_edit.text()
        name = self.name_edit.text().strip()

        if not login_id or not password or not name:
            QMessageBox.warning(self, "안내", "아이디, 비밀번호, 이름은 필수입니다.")
            return
        if not self._id_checked:
            QMessageBox.warning(self, "안내", "아이디 중복확인을 먼저 해주세요.")
            return
        if password != password_confirm:
            QMessageBox.warning(self, "안내", "비밀번호가 일치하지 않습니다.")
            return

        res = self.client.signup(
            login_id, password, name,
            address=self.address_edit.text().strip(),
            email=self.email_edit.text().strip(),
            phone=self.phone_edit.text().strip(),
            gender=self.gender_combo.currentData(),
        )

        if res.get("status") == "success":
            self.accept()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "회원가입에 실패했습니다."))
