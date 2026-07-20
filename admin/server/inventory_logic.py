from mysql.connector import Error

from inventory_DB import Database

class Inventory:
    def __init__(self):
        self.admin_id = "admin"

    # 관리자 권한 확인
    def check_admin(self, login_id):
        return login_id == self.admin_id

    # 재고수량에 따른 상태 반환
    def get_stock_status(self, stock):
        if stock == 0:
            return "품절"

        if stock <= 5:
            return "재고 부족"

        return "판매 가능"

    # 카테고리 목록 조회
    def get_category_list(self, login_id):
        if not self.check_admin(login_id):
            return {
                "type": "category_list",
                "success": False,
                "categories": [],
                "message": "관리자만 카테고리 목록을 조회할 수 있습니다."
            }
        connect = Database.get_connection()
        if connect is None:
            return {
                "type": "category_list",
                "success": False,
                "categories": [],
                "message": "DB연결 실패!"
            }
        cursor = None

        try:
            cursor = connect.cursor(dictionary=True)
            sql = """
                SELECT *
                FROM category
                ORDER BY category_id
            """
            cursor.execute(sql)
            categories = cursor.fetchall()

            print("[DB 카테고리 조회 결과]", categories)

            for category in categories:
                category["is_active"] = bool(category["is_active"])
            return {
                "type": "category_list",
                "success": True,
                "categories": categories,
                "message": "카테고리 목록을 조회했습니다."
            }

        except Error as err:
            print(f"카테고리 조회 오류 >> {err}")
            return {
                "type": "category_list",
                "success": False,
                "categories": [],
                "message": "카테고리 목록 조회에 실패했습니다."
            }

        finally:
            if cursor is not None:
                cursor.close()
            if connect.is_connected():
                connect.close()

    # 새로운 카테고리 추가
    def add_category(self, request, login_id):
        # 관리자 권한 확인
        if not self.check_admin(login_id):
            return {
                "type": "category_add",
                "success": False,
                "message": "관리자만 카테고리를 추가할 수 있습니다."
            }

        # 클라이언트가 전송한 카테고리명 가져오기
        name = request.get("name", "").strip()

        # 카테고리명 빈칸 검사
        if not name:
            return {
                "type": "category_add",
                "success": False,
                "message": "카테고리명을 입력하세요."
            }

        connection = Database.get_connection()

        # DB 연결 실패 확인
        if connection is None:
            return {
                "type": "category_add",
                "success": False,
                "message": "DB 연결에 실패했습니다."
            }

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            # 같은 이름의 카테고리가 존재하는지 확인
            duplicate_sql = """
                SELECT
                    category_id
                FROM category
                WHERE name = %s
            """

            cursor.execute(duplicate_sql, (name,))
            category = cursor.fetchone()

            if category is not None:
                return {
                    "type": "category_add",
                    "success": False,
                    "message": "이미 존재하는 카테고리명입니다."
                }

            # 새로운 카테고리 추가
            insert_sql = """
                INSERT INTO category (
                    name,
                    is_active
                )
                VALUES (
                    %s,
                    TRUE
                )
            """

            cursor.execute(insert_sql, (name,))
            category_id = cursor.lastrowid

            connection.commit()

            return {
                "type": "category_add",
                "success": True,
                "category_id": category_id,
                "message": "카테고리가 추가되었습니다."
            }

        except Error as error:
            connection.rollback()

            print(f"[카테고리 추가 오류] {error}")

            return {
                "type": "category_add",
                "success": False,
                "message": "카테고리 추가에 실패했습니다."
            }

        finally:
            if cursor is not None:
                cursor.close()

            if connection.is_connected():
                connection.close()

    # 기존 카테고리 정보 수정
    def update_category(self, request, login_id):
        # 관리자 권한 확인
        if not self.check_admin(login_id):
            return {
                "type": "category_update",
                "success": False,
                "message": "관리자만 카테고리를 수정할 수 있습니다."
            }

        # 클라이언트가 전송한 수정 정보 가져오기
        category_id = request.get("category_id")
        name = request.get("name", "").strip()
        is_active = request.get("is_active")

        # 카테고리 ID 검사
        if category_id is None:
            return {
                "type": "category_update",
                "success": False,
                "message": "카테고리 ID가 필요합니다."
            }

        # category_id 정수 검사
        if not isinstance(category_id, int):
            return {
                "type": "category_update",
                "success": False,
                "message": "카테고리 ID가 올바르지 않습니다."
            }

        # 카테고리명 검사
        if not name:
            return {
                "type": "category_update",
                "success": False,
                "message": "카테고리명을 입력하세요."
            }

        # 활성 여부 타입 검사
        if not isinstance(is_active, bool):
            return {
                "type": "category_update",
                "success": False,
                "message": "활성 상태 값이 올바르지 않습니다."
            }

        connection = Database.get_connection()

        if connection is None:
            return {
                "type": "category_update",
                "success": False,
                "message": "DB 연결에 실패했습니다."
            }
        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            # 수정 대상 카테고리가 존재하는지 확인
            find_sql = """
                SELECT
                    category_id
                FROM category
                WHERE category_id = %s
            """

            cursor.execute(find_sql, (category_id,))
            category = cursor.fetchone()

            if category is None:
                return {
                    "type": "category_update",
                    "success": False,
                    "message": "존재하지 않는 카테고리입니다."
                }

            # 다른 카테고리가 같은 이름을 사용하고 있는지 확인
            duplicate_sql = """
                SELECT
                    category_id
                FROM category
                WHERE name = %s
                  AND category_id != %s
            """

            cursor.execute(
                duplicate_sql,
                (name, category_id)
            )

            duplicate_category = cursor.fetchone()
            if duplicate_category is not None:
                return {
                    "type": "category_update",
                    "success": False,
                    "message": "이미 존재하는 카테고리명입니다."
                }

            # 카테고리명과 활성 상태 수정
            update_sql = """
                UPDATE category
                SET
                    name = %s,
                    is_active = %s
                WHERE category_id = %s
            """
            cursor.execute(
                update_sql,
                (
                    name,
                    is_active,
                    category_id
                )
            )

            connection.commit()

            return {
                "type": "category_update",
                "success": True,
                "category_id": category_id,
                "message": "카테고리가 수정되었습니다."
            }

        except Error as error:
            connection.rollback()
            print(f"[카테고리 수정 오류] {error}")
            return {
                "type": "category_update",
                "success": False,
                "message": "카테고리 수정에 실패했습니다."
            }

        finally:
            if cursor is not None:
                cursor.close()

            if connection.is_connected():
                connection.close()

    # 상품 목록 조회
    def get_product_list(self, login_id):
        # 관리자 권한 확인
        if not self.check_admin(login_id):
            return {
                "type": "inventory_product_list",
                "success": False,
                "products": [],
                "message": "관리자만 상품 목록을 조회할 수 있습니다."
            }

        connection = Database.get_connection()
        if connection is None:
            return {
                "type": "inventory_product_list",
                "success": False,
                "products": [],
                "message": "DB 연결에 실패했습니다."
            }

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            # 카테고리명과 함께 상품 목록 조회
            sql = """
                SELECT
                    p.product_id,
                    p.category_id,
                    c.name AS category_name,
                    p.name,
                    p.description,
                    p.color,
                    p.size,
                    p.price,
                    p.stock,
                    p.is_active,
                    p.created_at
                FROM product p
                INNER JOIN category c
                    ON p.category_id = c.category_id
                ORDER BY p.product_id 
            """

            cursor.execute(sql)
            products = cursor.fetchall()

            for product in products:
                # MySQL BOOLEAN 값을 Python bool로 변환
                product["is_active"] = bool(product["is_active"])

                # NULL 값을 빈 문자열로 변환
                product["description"] = product["description"] or ""
                product["color"] = product["color"] or ""
                product["size"] = product["size"] or ""

                # datetime 객체는 JSON 전송을 위해 문자열로 변환
                if product["created_at"] is not None:
                    product["created_at"] = product[
                        "created_at"
                    ].strftime("%Y-%m-%d %H:%M:%S")

                # 재고수량을 기준으로 재고 상태 추가
                product["stock_status"] = self.get_stock_status(
                    product["stock"]
                )

            return {
                "type": "inventory_product_list",
                "success": True,
                "products": products,
                "message": "상품 목록을 조회했습니다."
            }


        except Error as error:
            print(f"[상품 조회 오류] {error}")
            return {
                "type": "inventory_product_list",
                "success": False,
                "products": [],
                "message": f"상품 목록 조회 실패: {error}"
            }

        finally:
            if cursor is not None:
                cursor.close()

            if connection.is_connected():
                connection.close()

    # 새로운 상품 추가
    def add_product(self, request, login_id):
        # 관리자 권한 확인
        if not self.check_admin(login_id):
            return {
                "type": "product_add",
                "success": False,
                "message": "관리자만 상품을 추가할 수 있습니다."
            }

        # 상품 등록 정보 가져오기
        category_id = request.get("category_id")
        name = request.get("name", "").strip()
        description = request.get("description", "").strip()
        color = request.get("color", "").strip()
        size = request.get("size", "").strip()
        price = request.get("price")
        stock = request.get("inventory")

        # 카테고리 검사
        if not isinstance(category_id, int):
            return {
                "type": "product_add",
                "success": False,
                "message": "카테고리를 선택하세요."
            }

        # 상품명 검사
        if not name:
            return {
                "type": "product_add",
                "success": False,
                "message": "상품명을 입력하세요."
            }

        # 가격 검사
        if not isinstance(price, int) or isinstance(price, bool) or price < 0:
            return {
                "type": "product_add",
                "success": False,
                "message": "가격은 0 이상의 정수여야 합니다."
            }

        # 재고수량 검사
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            return {
                "type": "product_add",
                "success": False,
                "message": "재고수량은 0 이상의 정수여야 합니다."
            }

        # 입력하지 않은 선택 항목은 NULL로 저장
        description = description or None
        color = color or None
        size = size or None

        connection = Database.get_connection()

        if connection is None:
            return {
                "type": "product_add",
                "success": False,
                "message": "DB 연결에 실패했습니다."
            }

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            # 선택한 카테고리가 활성 상태인지 확인
            category_sql = """
                SELECT
                    category_id
                FROM category
                WHERE category_id = %s
                  AND is_active = TRUE
            """

            cursor.execute(category_sql, (category_id,))
            category = cursor.fetchone()

            if category is None:
                return {
                    "type": "product_add",
                    "success": False,
                    "message": "존재하지 않거나 비활성화된 카테고리입니다."
                }

            # 새로운 상품 등록
            insert_sql = """
                INSERT INTO product (
                    category_id,
                    name,
                    description,
                    color,
                    size,
                    price,
                    stock,
                    is_active
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
            """

            cursor.execute(
                insert_sql,
                (
                    category_id,
                    name,
                    description,
                    color,
                    size,
                    price,
                    stock
                )
            )

            product_id = cursor.lastrowid

            connection.commit()

            return {
                "type": "product_add",
                "success": True,
                "product_id": product_id,
                "stock_status": self.get_stock_status(stock),
                "message": "상품이 추가되었습니다."
            }

        except Error as error:
            connection.rollback()

            print(f"[상품 추가 오류] {error}")

            return {
                "type": "product_add",
                "success": False,
                "message": "상품 추가에 실패했습니다."
            }

        finally:
            if cursor is not None:
                cursor.close()

            if connection.is_connected():
                connection.close()

    # 기존 상품을 비활성화하고 새로운 상품 레코드 생성
    def update_product(self, request, login_id):
        # 관리자 권한 확인
        if not self.check_admin(login_id):
            return {
                "type": "product_update",
                "success": False,
                "message": "관리자만 상품을 수정할 수 있습니다."
            }

        # 상품 수정 정보 가져오기
        product_id = request.get("product_id")
        category_id = request.get("category_id")
        name = request.get("name", "").strip()
        description = request.get("description", "").strip()
        color = request.get("color", "").strip()
        size = request.get("size", "").strip()
        price = request.get("price")
        stock = request.get("inventory")

        # 기존 상품 ID 검사
        if not isinstance(product_id, int):
            return {
                "type": "product_update",
                "success": False,
                "message": "수정할 상품 ID가 필요합니다."
            }

        # 카테고리 검사
        if not isinstance(category_id, int):
            return {
                "type": "product_update",
                "success": False,
                "message": "카테고리를 선택하세요."
            }

        # 상품명 검사
        if not name:
            return {
                "type": "product_update",
                "success": False,
                "message": "상품명을 입력하세요."
            }

        # 가격 검사
        if not isinstance(price, int) or isinstance(price, bool) or price < 0:
            return {
                "type": "product_update",
                "success": False,
                "message": "가격은 0 이상의 정수여야 합니다."
            }

        # 재고수량 검사
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            return {
                "type": "product_update",
                "success": False,
                "message": "재고수량은 0 이상의 정수여야 합니다."
            }

        # 선택 입력값 빈 문자열을 NULL로 변경
        description = description or None
        color = color or None
        size = size or None

        connection = Database.get_connection()
        if connection is None:
            return {
                "type": "product_update",
                "success": False,
                "message": "DB 연결에 실패했습니다."
            }

        cursor = None

        try:
            # 상품 수정 전체 과정을 하나의 트랜잭션으로 처리
            connection.start_transaction()

            cursor = connection.cursor(dictionary=True)

            # 기존 상품을 조회하고 수정 중 다른 작업을 막기 위해 잠금
            product_sql = """
                SELECT
                    product_id
                FROM product
                WHERE product_id = %s
                  AND is_active = TRUE
                FOR UPDATE
            """

            cursor.execute(product_sql, (product_id,))
            product = cursor.fetchone()

            if product is None:
                connection.rollback()

                return {
                    "type": "product_update",
                    "success": False,
                    "message": "존재하지 않거나 비활성화된 상품입니다."
                }

            # 새 상품에 사용할 카테고리 상태 확인
            category_sql = """
                SELECT
                    category_id
                FROM category
                WHERE category_id = %s
                  AND is_active = TRUE
            """

            cursor.execute(category_sql, (category_id,))
            category = cursor.fetchone()

            if category is None:
                connection.rollback()

                return {
                    "type": "product_update",
                    "success": False,
                    "message": "존재하지 않거나 비활성화된 카테고리입니다."
                }

            # 기존 상품 비활성화
            deactivate_sql = """
                UPDATE product
                SET is_active = FALSE
                WHERE product_id = %s
                  AND is_active = TRUE
            """

            cursor.execute(deactivate_sql, (product_id,))

            # 기존 상품이 정상적으로 비활성화됐는지 확인
            if cursor.rowcount != 1:
                connection.rollback()

                return {
                    "type": "product_update",
                    "success": False,
                    "message": "기존 상품 비활성화에 실패했습니다."
                }

            # 수정된 상품 내용을 새로운 레코드로 추가
            insert_sql = """
                INSERT INTO product (
                    category_id,
                    name,
                    description,
                    color,
                    size,
                    price,
                    stock,
                    is_active
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
            """

            cursor.execute(
                insert_sql,
                (
                    category_id,
                    name,
                    description,
                    color,
                    size,
                    price,
                    stock
                )
            )

            new_product_id = cursor.lastrowid

            connection.commit()

            return {
                "type": "product_update",
                "success": True,
                "old_product_id": product_id,
                "new_product_id": new_product_id,
                "stock_status": self.get_stock_status(stock),
                "message": "기존 상품을 비활성화하고 새 상품을 등록했습니다."
            }

        except Error as error:
            connection.rollback()

            print(f"[상품 수정 오류] {error}")

            return {
                "type": "product_update",
                "success": False,
                "message": "상품 수정에 실패했습니다."
            }

        finally:
            if cursor is not None:
                cursor.close()

            if connection.is_connected():
                connection.close()

    # 주문 확정 시 여러 상품의 재고 차감
    def decrease_stock(self, request):
        # 주문 파트가 전달한 상품 목록 가져오기
        items = request.get("items", [])

        # 상품 목록 유효성 검사
        if not isinstance(items, list) or not items:
            return {
                "type": "stock_decrease",
                "success": False,
                "message": "재고를 차감할 상품 목록이 없습니다."
            }

        connection = Database.get_connection()

        if connection is None:
            return {
                "type": "stock_decrease",
                "success": False,
                "message": "DB 연결에 실패했습니다."
            }

        cursor = None

        try:
            # 모든 상품의 재고 차감을 하나의 트랜잭션으로 처리
            connection.start_transaction()

            cursor = connection.cursor(dictionary=True)

            for item in items:
                product_id = item.get("product_id")
                quantity = item.get("quantity")

                # 상품 ID 검사
                if not isinstance(product_id, int):
                    connection.rollback()

                    return {
                        "type": "stock_decrease",
                        "success": False,
                        "message": "상품 ID가 올바르지 않은 주문 항목이 있습니다."
                    }

                # 주문수량 검사
                if (
                    not isinstance(quantity, int)
                    or isinstance(quantity, bool)
                    or quantity <= 0
                ):
                    connection.rollback()

                    return {
                        "type": "stock_decrease",
                        "success": False,
                        "product_id": product_id,
                        "message": "주문수량은 1 이상의 정수여야 합니다."
                    }

                # 활성 상품이고 재고가 충분한 경우에만 재고 차감
                update_sql = """
                    UPDATE product
                    SET stock = stock - %s
                    WHERE product_id = %s
                      AND is_active = TRUE
                      AND stock >= %s
                """

                cursor.execute(
                    update_sql,
                    (
                        quantity,
                        product_id,
                        quantity
                    )
                )

                # 변경된 행이 없으면 상품이 없거나 재고가 부족한 상태
                if cursor.rowcount == 0:
                    connection.rollback()

                    return {
                        "type": "stock_decrease",
                        "success": False,
                        "product_id": product_id,
                        "message": "상품이 존재하지 않거나 재고가 부족합니다."
                    }

            connection.commit()

            return {
                "type": "stock_decrease",
                "success": True,
                "message": "주문 상품의 재고가 차감되었습니다."
            }

        except Error as error:
            connection.rollback()

            print(f"[재고 차감 오류] {error}")

            return {
                "type": "stock_decrease",
                "success": False,
                "message": "재고 차감에 실패했습니다."
            }

        finally:
            if cursor is not None:
                cursor.close()

            if connection.is_connected():
                connection.close()

    # 재고관리 요청 분기
    def handle_request(self, request, login_id):
        request_type = request.get("type", "")

        print("[재고관리 요청]", request)
        print("[요청 타입]", request_type)
        print("[로그인 아이디]", login_id)

        # 카테고리 목록 조회
        if request_type == "category_list":
            return self.get_category_list(login_id)

        # 카테고리 추가
        if request_type == "category_add":
            return self.add_category(request, login_id)

        # 카테고리 수정
        if request_type == "category_update":
            return self.update_category(request, login_id)

        # 관리자용 상품 목록 조회
        if request_type == "inventory_product_list":
            return self.get_product_list(login_id)

        # 상품 추가
        if request_type == "product_add":
            return self.add_product(request, login_id)

        # 상품 수정
        if request_type == "product_update":
            return self.update_product(request, login_id)

        # 주문 확정 시 재고 차감
        if request_type == "stock_decrease":
            return self.decrease_stock(request)

        # 지원하지 않는 요청
        return {
            "type": "error",
            "success": False,
            "message": f"지원하지 않는 재고관리 요청입니다: {request_type}"
        }