# handlers/product_handler.py
# B팀(상품페이지) 담당 action 처리 함수
#
# 모든 핸들러는 (cursor, request) -> response dict 형태로 통일한다.
# request는 클라이언트가 보낸 전체 딕셔너리({"action": ..., ...})

def handle_category_list(cursor, request):
    cursor.execute(
        "SELECT category_id, name FROM category WHERE is_active = TRUE ORDER BY category_id"
    )
    rows = cursor.fetchall()
    return {"status": "success", "data": rows}


def handle_product_list(cursor, request):
    category_id = request.get("category_id")
    keyword = request.get("keyword") or ""

    query = """
        SELECT p.product_id, p.name, p.color, p.size, p.price, p.stock
        FROM product p
        WHERE p.is_active = TRUE
    """
    params = []

    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)

    if keyword:
        query += " AND p.name LIKE %s"
        params.append(f"%{keyword}%")

    query += " ORDER BY p.product_id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return {"status": "success", "data": rows}


def handle_product_detail(cursor, request):
    product_id = request.get("product_id")
    if not product_id:
        return {"status": "fail", "message": "product_id가 필요합니다."}

    cursor.execute("""
        SELECT p.product_id, p.name, p.description, p.color, p.size,
               p.price, p.stock, c.name AS category_name
        FROM product p
        JOIN category c ON p.category_id = c.category_id
        WHERE p.product_id = %s AND p.is_active = TRUE
    """, (product_id,))
    row = cursor.fetchone()

    if not row:
        return {"status": "fail", "message": "상품을 찾을 수 없습니다."}

    return {"status": "success", "data": row}


# 서버 메인에서 이 딕셔너리를 가져다가 다른 팀 핸들러와 합치면 됨
PRODUCT_ACTION_HANDLERS = {
    "category_list": handle_category_list,
    "product_list": handle_product_list,
    "product_detail": handle_product_detail,
}
