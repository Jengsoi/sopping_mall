import  mysql.connector

class Database:
    config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "1234",
        "database": "shopping",
        "charset": "utf8"
    }
    @classmethod
    def get_connection(cls):
        try:
            connection = mysql.connector.connect(**cls.config)
            return connection

        except mysql.connector.Error as err:
            print(err)
            return None