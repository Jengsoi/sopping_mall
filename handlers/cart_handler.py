# handlers/cart_handler.py
# C팀(장바구니/주문처리) 담당 action 처리 함수
#
# member_id는 항상 request에서 꺼내온다. server.py의 process_request가
# 로그인 세션이 있으면 자동으로 request["member_id"]를 채워주므로,
# 여기서는 "없으면 로그인이 필요합니다" 로만 처리하면 된다.


def handle_cart_list(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    cursor.execute("""
        SELECT cart.cart_id, cart.product_id, product.name, product.price, cart.quantity
        FROM cart
        JOIN product ON cart.product_id = product.product_id
        WHERE cart.member_id = %s
        ORDER BY cart.cart_id
    """, (member_id,))
    rows = cursor.fetchall()
    return {"status": "success", "data": rows}


def handle_cart_add(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    product_id = request.get("product_id")
    quantity = request.get("quantity", 1)

    if not product_id:
        return {"status": "fail", "message": "product_id가 필요합니다."}

    cursor.execute("SELECT stock FROM product WHERE product_id = %s AND is_active = TRUE", (product_id,))
    product = cursor.fetchone()
    if not product:
        return {"status": "fail", "message": "존재하지 않는 상품입니다."}
    if product["stock"] < quantity:
        return {"status": "fail", "message": f"재고가 부족합니다. (남은 재고: {product['stock']}개)"}

    # cart 테이블에 UNIQUE(member_id, product_id) 걸려있어서,
    # 이미 담긴 상품이면 수량만 더해준다.
    cursor.execute("""
        INSERT INTO cart (member_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
    """, (member_id, product_id, quantity))

    return {"status": "success", "message": "장바구니에 담았습니다."}


def handle_cart_update(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    cart_id = request.get("cart_id")
    quantity = request.get("quantity")

    if not cart_id or quantity is None:
        return {"status": "fail", "message": "cart_id, quantity가 필요합니다."}
    if quantity <= 0:
        return {"status": "fail", "message": "수량은 1개 이상이어야 합니다."}

    cursor.execute(
        "UPDATE cart SET quantity = %s WHERE cart_id = %s AND member_id = %s",
        (quantity, cart_id, member_id)
    )
    return {"status": "success", "message": "수량이 변경되었습니다."}


def handle_cart_delete(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    cart_id = request.get("cart_id")

    if not cart_id:
        return {"status": "fail", "message": "cart_id가 필요합니다."}

    cursor.execute(
        "DELETE FROM cart WHERE cart_id = %s AND member_id = %s",
        (cart_id, member_id)
    )
    return {"status": "success", "message": "삭제되었습니다."}


def handle_order_create(cursor, request):
    """
    request['order_items'] 형식:
        [{"cart_id": 3, "product_id": 7, "quantity": 2}, ...]

    cart_id가 있으면 주문 완료 후 해당 장바구니 행을 같이 삭제한다.
    (전체구매/선택구매 둘 다 이 하나의 action으로 처리)
    """
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    order_items = request.get("order_items", [])

    if not order_items:
        return {"status": "fail", "message": "주문할 상품이 없습니다."}

    cursor.execute(
        "INSERT INTO orders (member_id, status) VALUES (%s, 'PAID')",
        (member_id,)
    )
    order_id = cursor.lastrowid

    for item in order_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity")

        # 최신 상품명/가격/재고를 서버에서 직접 조회 (클라이언트 값을 그대로 믿지 않음)
        cursor.execute(
            "SELECT name, price, stock FROM product WHERE product_id = %s AND is_active = TRUE",
            (product_id,)
        )
        product = cursor.fetchone()

        if not product:
            raise ValueError(f"상품(product_id={product_id})을 찾을 수 없습니다.")
        if product["stock"] < quantity:
            raise ValueError(f"{product['name']} 재고가 부족합니다. (남은 재고: {product['stock']}개)")

        cursor.execute("""
            INSERT INTO order_item (order_id, product_id, product_name, price, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, product_id, product["name"], product["price"], quantity))

        cursor.execute(
            "UPDATE product SET stock = stock - %s WHERE product_id = %s",
            (quantity, product_id)
        )

        cart_id = item.get("cart_id")
        if cart_id:
            cursor.execute(
                "DELETE FROM cart WHERE cart_id = %s AND member_id = %s",
                (cart_id, member_id)
            )

    return {"status": "success", "data": {"order_id": order_id}}


def handle_order_list(cursor, request):
    member_id = request.get("member_id")
    if not member_id:
        return {"status": "fail", "message": "로그인이 필요합니다."}

    cursor.execute("""
        SELECT order_id, status, ordered_at
        FROM orders
        WHERE member_id = %s
        ORDER BY order_id DESC
    """, (member_id,))
    rows = cursor.fetchall()
    return {"status": "success", "data": rows}


def handle_order_detail(cursor, request):
    order_id = request.get("order_id")
    if not order_id:
        return {"status": "fail", "message": "order_id가 필요합니다."}

    cursor.execute(
        "SELECT order_id, member_id, status, ordered_at FROM orders WHERE order_id = %s",
        (order_id,)
    )
    order = cursor.fetchone()
    if not order:
        return {"status": "fail", "message": "주문을 찾을 수 없습니다."}

    cursor.execute("""
        SELECT order_item_id, product_id, product_name, price, quantity
        FROM order_item
        WHERE order_id = %s
    """, (order_id,))
    items = cursor.fetchall()

    order["items"] = items
    return {"status": "success", "data": order}


CART_ACTION_HANDLERS = {
    "cart_list": handle_cart_list,
    "cart_add": handle_cart_add,
    "cart_update": handle_cart_update,
    "cart_delete": handle_cart_delete,
    "order_create": handle_order_create,
    "order_list": handle_order_list,
    "order_detail": handle_order_detail,
}
