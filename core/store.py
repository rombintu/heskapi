from sys import exit
from ast import literal_eval
import json 


from utils.logger import logger as log
from core.config import Tables, statuses
import pymysql.cursors


class StoreCreds:
    def __init__(self, 
                 host: str, 
                 user: str,
                 password: str,
                 database: str,
                ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

        if self.check_empty():
            log.error("MYSQL env are not set, read README.md")

    def check_empty(self):
        return None in [
            self.host, 
            self.user, 
            self.password, 
            self.database,
        ]


    
class Store:
    def __init__(self, c: StoreCreds):
        # Connect to the database
        self.connection = pymysql.connect(host=c.host,
                                    user=c.user,
                                    password=c.password,
                                    database=c.database,
                                    cursorclass=pymysql.cursors.DictCursor)
        
    def check_version(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchall()
            return version
    
    def get_tables(self):
        with self.connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            result = cursor.fetchall()
            return result

    def users_get(self):
        with self.connection.cursor() as cursor:
            sql = f"SELECT id, user, isadmin, name, email FROM {Tables.users.value}"
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        
    def user_get(self, user_id: int):
        with self.connection.cursor() as cursor:
            sql = f"SELECT id, user, isadmin, name, email FROM {Tables.users.value} WHERE id=%s"
            cursor.execute(sql, (user_id))
            result = cursor.fetchone()
            return result

    def tickets_user_owner_without_status(self, user_id: int, skip_status_id: int = 3):
        """Default: get tickets without status RESOLVED
        statuses = {
            0: "Новая",
            1: "Получен комментарий",
            2: "Комментарий отправлен",
            3: "Решена",
            4: "В работе",
            5: "Приостановлена",
        } 
        AND CUSTOM_FIELDS FROM DATABASE
        """
        # filter_status = self.ticket_status_get(status_id)
        
        with self.connection.cursor() as cursor:
            sql = f"""
                SELECT ht.*, hu.name AS owner_name, hc.name AS category_name
                FROM {Tables.tickets.value} ht
                    LEFT JOIN {Tables.users.value} hu
                        ON ht.owner = hu.id
                    LEFT JOIN {Tables.categories.value} hc
                        ON ht.category = hc.id
                    WHERE hu.id=%s AND ht.status != %s"""
            cursor.execute(sql, (user_id, skip_status_id))
            result = cursor.fetchall()
            return result

    def ticket_get(self, ticket_id: int):
        with self.connection.cursor() as cursor:
            sql = f"""
                SELECT ht.*, hu.name AS owner_name, hc.name AS category_name
                FROM {Tables.tickets.value} ht
                    LEFT JOIN {Tables.users.value} hu
                        ON ht.owner = hu.id
                    LEFT JOIN {Tables.categories.value} hc
                        ON ht.category = hc.id
                    WHERE ht.id=%s
                    LIMIT 1"""
            cursor.execute(sql, (ticket_id))
            result = cursor.fetchone()
            if result and result.get("status"):
                status = self.ticket_status_get(result["status"])
                result["status"] = status
            return result
    
    def ticket_get_by_track_id(self, track_id: int):
        with self.connection.cursor() as cursor:
            sql = f"""
                SELECT ht.*, hu.name AS owner_name, hc.name AS category_name
                FROM {Tables.tickets.value} ht
                    LEFT JOIN {Tables.users.value} hu
                        ON ht.owner = hu.id
                    LEFT JOIN {Tables.categories.value} hc
                        ON ht.category = hc.id
                    WHERE ht.trackid=%s
                    LIMIT 1"""
            cursor.execute(sql, (track_id))
            result = cursor.fetchone()
            if result and result.get("status"):
                status = self.ticket_status_get(result["status"])
                result["status"] = status
            return result

    def tickets_get(self):
        with self.connection.cursor() as cursor:
            sql = f"""SELECT * FROM {Tables.tickets.value}"""
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
    
    def ticket_status_get(self, status_id: int):
        result = statuses.get(status_id)
        if not result:
            result = "Нет статуса"
            with self.connection.cursor() as cursor:
                sql = f"""
                    SELECT name FROM {Tables.custom_statutes.value}
                    WHERE id=%s"""
                cursor.execute(sql, (status_id))
                status = cursor.fetchone()
                if status:
                    result = status.get('name')
        return result
    
    def ticket_get_custom_fields(self, ticket: dict):
        custom_fields_original = self.mapping_category2custom_flds(ticket.get("category"))
        cf_values_from_ticket = []
        for k, v in ticket.items():
            if k.startswith('custom') and v:
                cf_values_from_ticket.append({
                    "id": int(k.replace('custom', '')),
                    "name": None,
                    "value": v,
                    })
        for cf in cf_values_from_ticket:
            for cfo in custom_fields_original:
                if cfo['id'] == cf['id']:
                    cf['name'] = cfo['name']
        return cf_values_from_ticket


    def categories_get(self):
        with self.connection.cursor() as cursor:
            sql = f"""SELECT * FROM {Tables.categories.value}"""
            cursor.execute(sql)
            result = cursor.fetchall()
            return result

    def category_get(self, category_id: int):
        with self.connection.cursor() as cursor:
            sql = f"""SELECT * FROM {Tables.categories.value} WHERE id=%s"""
            cursor.execute(sql, (category_id))
            result = cursor.fetchone()
            return result
        
    def custom_fields_get(self):
        with self.connection.cursor() as cursor:
            sql = f"""SELECT * FROM {Tables.custom_fields.value}"""
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        
    def custom_field_get(self, custom_field_id):
        with self.connection.cursor() as cursor:
            sql = f"""SELECT * FROM {Tables.custom_fields.value} WHERE id=%s"""
            cursor.execute(sql, (custom_field_id))
            result = cursor.fetchone()
            return result

    def mapping_category2custom_flds(self, category_id: int):
        with self.connection.cursor() as cursor:
            sql = f"""SELECT * FROM {Tables.custom_fields.value} 
                        WHERE `use`=%s
                        ORDER BY id"""
            cursor.execute(sql, (2))
            result = cursor.fetchall()
            payload = []
            for row in result:
                category_list: list = literal_eval(row.get('category'))
                if str(category_id) in category_list:
                    payload.append(row)
                    row["name"] = list(json.loads(row.get("name")).values())[0]
                    row["value"] = json.loads(row.get("value"))
            return payload

# with connection:
#     with connection.cursor() as cursor:
#         # Create a new record
#         sql = "INSERT INTO `users` (`email`, `password`) VALUES (%s, %s)"
#         cursor.execute(sql, ('webmaster@python.org', 'very-secret'))

#     # connection is not autocommit by default. So you must commit to save
#     # your changes.
#     connection.commit()

    