import socket
import mysql.connector
import threading

from dashboard_protocol import Protocol

class DashboardServer:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port

        self.proto = Protocol()

    def connect_to_db(self):
        return mysql.connector.connect(
                host = "localhost",
                port = 3306,
                user = "root",
                password = "1234",
                database = "shopping",
                charset = "utf8mb4",
            )

    def client_handle(self, client_socket, client_addr):
        print(f"[{client_addr}] 처리중...")
        buffer = ""

        while True:
            buffer, messages, connected = self.proto.receive_message(client_socket, buffer)

            if not connected:
                print("서버와 접속이 실패했습니다.")
                break

            for message in messages:
                message_type = message.get("type", "")
                start = message.get("start", "")
                end = message.get("end", "")

                if message_type == "data":
                    send_total_sales = self.get_total_sales(start, end)
                    self.proto.send_message(client_socket,{
                        "type": "total_sales",
                        "content": send_total_sales,
                    })

                    send_product_top5 = self.get_product_top5(start, end)
                    self.proto.send_message(client_socket,{
                        "type": "product_top5",
                        "content": send_product_top5,
                    })

                    send_category_sales = self.get_category_sales(start, end)
                    self.proto.send_message(client_socket,{
                        "type": "category_sales",
                        "content": send_category_sales,
                    })

    def get_total_sales(self, start, end):

        conn = None
        cursor = None

        try:
            conn = self.connect_to_db()
            #if conn: print("DB 접속 성공!!")

            cursor = conn.cursor(dictionary=True)

            query = """
            
                    SELECT 
                        CAST(SUM(oi.price * oi.quantity) AS CHAR) AS total_sales
                    FROM
                        orders o
                    JOIN
                        order_item oi ON o.order_id = oi.order_id
                    WHERE
                        o.ordered_at BETWEEN %s AND %s
            """

            cursor.execute(query, (start, end))
            return cursor.fetchall()

        except mysql.connector.Error as error:
            print(f"DB 접속 실패 {error}")

        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_product_top5(self, start, end):

        conn = None
        cursor = None

        try:
            conn = self.connect_to_db()

            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    product_name, 
                    CAST(SUM(oi.price * oi.quantity) AS CHAR) AS total_sales
                FROM orders o
                JOIN order_item oi ON o.order_id = oi.order_id
                WHERE o.ordered_at BETWEEN %s AND %s
                GROUP BY oi.product_name
                ORDER BY SUM(oi.price * oi.quantity) DESC
                LIMIT 5
            """

            cursor.execute(query, (start, end))
            return cursor.fetchall()

        except mysql.connector.Error as error:
            print(f"DB 접속 실패 {error}")

        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_category_sales(self, start, end):
        conn = None
        cursor = None

        try:
            conn = self.connect_to_db()
            #if conn: print("DB 접속 성공!!")

            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    c.name, 
                    CAST(SUM(oi.price * oi.quantity) AS CHAR) AS total_sales
                FROM category c
                JOIN product p ON c.category_id = p.category_id
                JOIN order_item oi ON p.product_id = oi.product_id
                JOIN orders o ON oi.order_id = o.order_id
                WHERE o.ordered_at BETWEEN %s AND %s
                GROUP BY c.category_id
            """

            cursor.execute(query, (start, end))
            return cursor.fetchall()

        except mysql.connector.Error as error:
            print(f"DB 접속 실패 {error}")

        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host,self.port))
        server_socket.listen()

        print("클라이언트 접속 대기중...")

        while True:
            client_socket, client_addr = server_socket.accept()

            receive_thread = threading.Thread(
                target=self.client_handle,
                args=(client_socket, client_addr),
                daemon=True
            )
            receive_thread.start()

if __name__ == '__main__':
    server = DashboardServer()
    server.run()