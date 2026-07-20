# auth/gui/member_view.py
# 로그인 성공 후 보여주는 내 정보 화면 - PySide6
# 회원정보 수정 / 회원탈퇴 / 로그아웃을 처리한다.

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QComboBox, QPushButton, QLabel,
    QFormLayout, QVBoxLayout, QHBoxLayout, QMessageBox,
)


class MemberView(QWidget):
    logout_requested = Signal()

    def __init__(self, client, member):
        super().__init__()
        self.client = client
        self.member = member

        self._build_ui()
        self.load_info()

    def _build_ui(self):
        self.greeting_label = QLabel()

        self.login_id_label = QLabel()
        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("선택 안 함", "")
        self.gender_combo.addItem("남성", "M")
        self.gender_combo.addItem("여성", "F")

        form = QFormLayout()
        form.addRow("아이디", self.login_id_label)
        form.addRow("이름", self.name_edit)
        form.addRow("주소", self.address_edit)
        form.addRow("이메일", self.email_edit)
        form.addRow("전화번호", self.phone_edit)
        form.addRow("성별", self.gender_combo)

        btn_update = QPushButton("정보수정")
        btn_withdraw = QPushButton("회원탈퇴")
        btn_logout = QPushButton("로그아웃")
        btn_update.clicked.connect(self.on_update)
        btn_withdraw.clicked.connect(self.on_withdraw)
        btn_logout.clicked.connect(self.on_logout)

        button_row = QHBoxLayout()
        button_row.addWidget(btn_update)
        button_row.addWidget(btn_withdraw)
        button_row.addWidget(btn_logout)

        layout = QVBoxLayout()
        layout.addWidget(self.greeting_label)
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addStretch()
        self.setLayout(layout)

    def load_info(self):
        res = self.client.member_info()
        if res.get("status") != "success":
            QMessageBox.warning(self, "오류", res.get("message", "회원정보 조회 실패"))
            return

        info = res["data"]
        self.greeting_label.setText(f'{info["name"]}님 환영합니다.')
        self.login_id_label.setText(info["login_id"])
        self.name_edit.setText(info["name"])
        self.address_edit.setText(info.get("address") or "")
        self.email_edit.setText(info.get("email") or "")
        self.phone_edit.setText(info.get("phone") or "")

        gender = info.get("gender") or ""
        index = self.gender_combo.findData(gender)
        self.gender_combo.setCurrentIndex(index if index >= 0 else 0)

    def on_update(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "안내", "이름을 입력하세요.")
            return

        res = self.client.member_update(
            name=name,
            address=self.address_edit.text().strip(),
            email=self.email_edit.text().strip(),
            phone=self.phone_edit.text().strip(),
            gender=self.gender_combo.currentData(),
        )

        if res.get("status") == "success":
            QMessageBox.information(self, "안내", "회원정보가 수정되었습니다.")
            self.load_info()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "수정에 실패했습니다."))

    def on_withdraw(self):
        confirm = QMessageBox.question(
            self, "회원탈퇴", "정말 탈퇴하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        res = self.client.member_withdraw()
        if res.get("status") == "success":
            QMessageBox.information(self, "안내", "회원탈퇴가 완료되었습니다.")
            self.logout_requested.emit()
        else:
            QMessageBox.warning(self, "오류", res.get("message", "탈퇴에 실패했습니다."))

    def on_logout(self):
        self.client.logout()
        self.logout_requested.emit()
