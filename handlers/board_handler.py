# board/handlers/board_handler.py
# F팀(게시판 관리) 담당 action 처리 함수
#
# 모든 핸들러는 (cursor, request) -> response dict 형태로 통일한다.
# request는 클라이언트가 보낸 전체 딕셔너리({"action": ..., ...})
#
# ★ 임시 처리: 아직 A팀(로그인) 세션이 없어서, member_id는 요청에 없으면
#   기본값 1번 회원으로 처리합니다. A팀 로그인이 완성되면
#   request.get("member_id", CURRENT_MEMBER_ID) 부분을
#   실제 로그인 세션에서 꺼낸 member_id로 바꿔주세요.

CURRENT_MEMBER_ID = 1  # TODO: A팀 로그인 완성되면 세션 기반으로 교체


def handle_board_list(cursor, request):
    page = request.get("page") or 1
    size = request.get("size") or 20
    keyword = (request.get("keyword") or "").strip()
    offset = (page - 1) * size

    where_clause = ""
    params = []
    if keyword:
        where_clause = "WHERE bp.title LIKE %s"
        params.append(f"%{keyword}%")

    cursor.execute(f"SELECT COUNT(*) AS total FROM board_post bp {where_clause}", params)
    total = cursor.fetchone()["total"]

    cursor.execute(f"""
        SELECT bp.post_id, bp.title, bp.created_at, m.name AS author,
               (SELECT COUNT(*) FROM comment c WHERE c.post_id = bp.post_id) AS comment_count
        FROM board_post bp
        JOIN member m ON bp.member_id = m.member_id
        {where_clause}
        ORDER BY bp.post_id DESC
        LIMIT %s OFFSET %s
    """, params + [size, offset])
    rows = cursor.fetchall()

    return {"status": "success", "data": {"posts": rows, "total": total, "page": page, "size": size}}


def handle_board_detail(cursor, request):
    post_id = request.get("post_id")
    if not post_id:
        return {"status": "fail", "message": "post_id가 필요합니다."}

    cursor.execute("""
        SELECT bp.post_id, bp.member_id, bp.title, bp.content, bp.created_at, m.name AS author
        FROM board_post bp
        JOIN member m ON bp.member_id = m.member_id
        WHERE bp.post_id = %s
    """, (post_id,))
    post = cursor.fetchone()
    if not post:
        return {"status": "fail", "message": "게시글을 찾을 수 없습니다."}

    cursor.execute("""
        SELECT c.comment_id, c.member_id, c.content, c.created_at, m.name AS author
        FROM comment c
        JOIN member m ON c.member_id = m.member_id
        WHERE c.post_id = %s
        ORDER BY c.comment_id
    """, (post_id,))
    post["comments"] = cursor.fetchall()

    return {"status": "success", "data": post}


def handle_board_create(cursor, request):
    member_id = request.get("member_id", CURRENT_MEMBER_ID)
    title = (request.get("title") or "").strip()
    content = request.get("content") or ""

    if not title:
        return {"status": "fail", "message": "제목을 입력하세요."}

    cursor.execute(
        "INSERT INTO board_post (member_id, title, content) VALUES (%s, %s, %s)",
        (member_id, title, content)
    )
    return {"status": "success", "data": {"post_id": cursor.lastrowid}}


def handle_board_update(cursor, request):
    member_id = request.get("member_id", CURRENT_MEMBER_ID)
    post_id = request.get("post_id")
    title = request.get("title")
    content = request.get("content")

    if not post_id:
        return {"status": "fail", "message": "post_id가 필요합니다."}

    cursor.execute("SELECT member_id FROM board_post WHERE post_id = %s", (post_id,))
    post = cursor.fetchone()
    if not post:
        return {"status": "fail", "message": "게시글을 찾을 수 없습니다."}
    if post["member_id"] != member_id:
        return {"status": "fail", "message": "작성자만 수정할 수 있습니다."}

    fields = []
    params = []
    if title is not None:
        title = title.strip()
        if not title:
            return {"status": "fail", "message": "제목을 입력하세요."}
        fields.append("title = %s")
        params.append(title)
    if content is not None:
        fields.append("content = %s")
        params.append(content)

    if not fields:
        return {"status": "fail", "message": "수정할 내용이 없습니다."}

    params.append(post_id)
    cursor.execute(f"UPDATE board_post SET {', '.join(fields)} WHERE post_id = %s", params)
    return {"status": "success", "message": "게시글이 수정되었습니다."}


def handle_board_delete(cursor, request):
    member_id = request.get("member_id", CURRENT_MEMBER_ID)
    post_id = request.get("post_id")

    if not post_id:
        return {"status": "fail", "message": "post_id가 필요합니다."}

    cursor.execute("SELECT member_id FROM board_post WHERE post_id = %s", (post_id,))
    post = cursor.fetchone()
    if not post:
        return {"status": "fail", "message": "게시글을 찾을 수 없습니다."}
    if post["member_id"] != member_id:
        return {"status": "fail", "message": "작성자만 삭제할 수 있습니다."}

    cursor.execute("DELETE FROM comment WHERE post_id = %s", (post_id,))
    cursor.execute("DELETE FROM board_post WHERE post_id = %s", (post_id,))
    return {"status": "success", "message": "게시글이 삭제되었습니다."}


def handle_comment_create(cursor, request):
    member_id = request.get("member_id", CURRENT_MEMBER_ID)
    post_id = request.get("post_id")
    content = (request.get("content") or "").strip()

    if not post_id:
        return {"status": "fail", "message": "post_id가 필요합니다."}
    if not content:
        return {"status": "fail", "message": "댓글 내용을 입력하세요."}

    cursor.execute("SELECT post_id FROM board_post WHERE post_id = %s", (post_id,))
    if not cursor.fetchone():
        return {"status": "fail", "message": "게시글을 찾을 수 없습니다."}

    cursor.execute(
        "INSERT INTO comment (post_id, member_id, content) VALUES (%s, %s, %s)",
        (post_id, member_id, content)
    )
    return {"status": "success", "data": {"comment_id": cursor.lastrowid}}


def handle_comment_update(cursor, request):
    member_id = request.get("member_id", CURRENT_MEMBER_ID)
    comment_id = request.get("comment_id")
    content = (request.get("content") or "").strip()

    if not comment_id:
        return {"status": "fail", "message": "comment_id가 필요합니다."}
    if not content:
        return {"status": "fail", "message": "댓글 내용을 입력하세요."}

    cursor.execute("SELECT member_id FROM comment WHERE comment_id = %s", (comment_id,))
    comment = cursor.fetchone()
    if not comment:
        return {"status": "fail", "message": "댓글을 찾을 수 없습니다."}
    if comment["member_id"] != member_id:
        return {"status": "fail", "message": "작성자만 수정할 수 있습니다."}

    cursor.execute("UPDATE comment SET content = %s WHERE comment_id = %s", (content, comment_id))
    return {"status": "success", "message": "댓글이 수정되었습니다."}


def handle_comment_delete(cursor, request):
    member_id = request.get("member_id", CURRENT_MEMBER_ID)
    comment_id = request.get("comment_id")

    if not comment_id:
        return {"status": "fail", "message": "comment_id가 필요합니다."}

    cursor.execute("SELECT member_id FROM comment WHERE comment_id = %s", (comment_id,))
    comment = cursor.fetchone()
    if not comment:
        return {"status": "fail", "message": "댓글을 찾을 수 없습니다."}
    if comment["member_id"] != member_id:
        return {"status": "fail", "message": "작성자만 삭제할 수 있습니다."}

    cursor.execute("DELETE FROM comment WHERE comment_id = %s", (comment_id,))
    return {"status": "success", "message": "댓글이 삭제되었습니다."}


# 서버 메인에서 이 딕셔너리를 가져다가 다른 팀 핸들러와 합치면 됨
BOARD_ACTION_HANDLERS = {
    "board_list": handle_board_list,
    "board_detail": handle_board_detail,
    "board_create": handle_board_create,
    "board_update": handle_board_update,
    "board_delete": handle_board_delete,
    "comment_create": handle_comment_create,
    "comment_update": handle_comment_update,
    "comment_delete": handle_comment_delete,
}
