# auth/handlers/auth_handler.py
# A팀(회원가입/로그인) 담당 action 처리 함수
#
# 모든 핸들러는 (cursor, request) -> response dict 형태로 통일한다.
# request는 클라이언트가 보낸 전체 딕셔너리({"action": ..., ...})
#
# 로그인 세션(member_id) 자체는 이 파일에서 관리하지 않는다.
# server.py 가 연결(소켓)마다 세션을 들고 있다가, login 성공 응답의
# data.member_id 를 세션에 저장하고, 그 다음부터는 요청에 member_id가
# 없으면 자동으로 채워서 넘겨준다. (server.py의 process_request 참고)

import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def handle_signup(cursor, request):
    login_id = (request.get("login_id") or "").strip()
    password = request.get("password") or ""
    name = (request.get("name") or "").strip()
    address = request.get("address") or ""
    email = request.get("email") or ""
    phone = request.get("phone") or ""
    gender = request.get("gender") or ""

    if not login_id or not password or not name:
        return {"status": "fail", "message": "아이디, 비밀번호, 이름은 필수입니다."}

    cursor.execute("SELECT member_id FROM member WHERE login_id = %s", (login_id,))
    if cursor.fetchone():
        return {"status": "fail", "message": "이미 사용 중인 아이디입니다."}

    cursor.execute("""
        INSERT INTO member (login_id, password, name, address, email, phone, gender)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (login_id, hash_password(password), name, address, email, phone, gender))

    return {"status": "success", "data": {"member_id": cursor.lastrowid}}


def handle_check_id(cursor, request):
    login_id = (request.get("login_id") or "").strip()
    if not login_id:
        return {"status": "fail", "message": "login_id가 필요합니다."}

    cursor.execute("SELECT member_id FROM member WHERE login_id = %s", (login_id,))
    exists = cursor.fetchone() is not None
    return {"status": "success", "data": {"available": not exists}}


def handle_login(cursor, request):
    login_id = (request.get("login_id") or "").strip()
    password = request.get("password") or ""

    if not login_id or not password:
        return {"status": "fail", "message": "아이디와 비밀번호를 입력하세요."}

    cursor.execute(
        "SELECT member_id, login_id, name, password, is_active, role FROM member WHERE login_id = %s",
        (login_id,)
    )
    member = cursor.fetchone()

    if not member or member["password"] != hash_password(password):
        return {"status": "fail", "message": "아이디 또는 비밀번호가 올바르지 않습니다."}
    if not member["is_active"]:
        return {"status": "fail", "message": "탈퇴한 계정입니다."}

    return {
        "status": "success",
        "data": {
            "member_id": member["member_id"],
            "login_id": member["login_id"],
            "name": member["name"],
            "role": member["role"],
        },
    }


def handle_logout(cursor, request):
    # 실제 세션 초기화는 server.py 의 process_request 에서 처리한다.
    return {"status": "success", "message": "로그아웃 되었습니다."}


def handle_member_info(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    cursor.execute("""
        SELECT member_id, login_id, name, address, email, phone, gender, role, created_at
        FROM member
        WHERE member_id = %s AND is_active = TRUE
    """, (member_id,))
    row = cursor.fetchone()
    if not row:
        return {"status": "fail", "message": "회원을 찾을 수 없습니다."}

    return {"status": "success", "data": row}


def handle_member_update(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    fields = []
    params = []
    for column in ("name", "address", "email", "phone", "gender"):
        value = request.get(column)
        if value is not None:
            fields.append(f"{column} = %s")
            params.append(value)

    if not fields:
        return {"status": "fail", "message": "수정할 내용이 없습니다."}

    params.append(member_id)
    cursor.execute(f"UPDATE member SET {', '.join(fields)} WHERE member_id = %s", params)
    return {"status": "success", "message": "회원정보가 수정되었습니다."}


def handle_member_withdraw(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    cursor.execute("UPDATE member SET is_active = FALSE WHERE member_id = %s", (member_id,))
    return {"status": "success", "message": "회원 탈퇴가 완료되었습니다."}


# 서버 메인에서 이 딕셔너리를 가져다가 다른 팀 핸들러와 합치면 됨
AUTH_ACTION_HANDLERS = {
    "signup": handle_signup,
    "check_id": handle_check_id,
    "login": handle_login,
    "logout": handle_logout,
    "member_info": handle_member_info,
    "member_update": handle_member_update,
    "member_withdraw": handle_member_withdraw,
}
