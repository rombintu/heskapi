from sys import exit
from ast import literal_eval
import json 


from utils.logger import logger as log
from core.config import Tables, statuses
import pymysql.cursors
from pymysql.err import IntegrityError, OperationalError
from pydantic import BaseModel

class Client(BaseModel):
    telegram_id: int
    email: str
    username: str | None
    fio: str 

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
        self.connection = None
        self.creds = c
        self.create_table_for_api()

    def open(self):
        if not self.connection:
            try:
                self.connection = pymysql.connect(host=self.creds.host,
                    user=self.creds.user,
                    password=self.creds.password,
                    database=self.creds.database,
                    cursorclass=pymysql.cursors.DictCursor)
            except OperationalError as err:
                log.error(f'Ошибка подключения к Базе данных: {err}')
                self.connection = None
        self.connection
    
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, sql_script, params=None, all=False, commit=False):
        log.debug(f"{sql_script} | {params}")
        self.open()
        if self.connection:
            try:
                with self.connection.cursor() as c:
                    c.execute(sql_script, params)
                    if commit:
                        self.connection.commit()
                    if all:
                        return c.fetchall()
                    else:
                        return c.fetchone()
            except Exception as err:
                log.error(f"Ошибка выполнения запроса: {err}")
            finally:
                self.close()

    def execute_select_one(self, sql_script, params=None):
        return self.execute(sql_script, params)
        
    def execute_select_all(self, sql_script, params=None):
        return self.execute(sql_script, params, all=True)
    
    def execute_with_commit(self, sql_script, params=None):
        self.execute(sql_script, params, commit=True)

    def check_version(self):
        return self.execute_select_all("SELECT VERSION()")
    
    def get_tables(self):
        return self.execute_select_all("SHOW TABLES")
    
    def users_get(self):
        return self.execute_select_all(
            f"SELECT id, user, isadmin, name, email FROM {Tables.users.value}")
        
    def user_get(self, user_id: int):
        return self.execute_select_one(
            f"SELECT id, user, isadmin, name, email FROM {Tables.users.value} WHERE id=%s",
            params=(user_id)
        )

    # TODO
    def users_get_workloaded(self):
        sql = f"""
            SELECT hu.id, COUNT(ht.status) AS inprogress
            FROM {Tables.users.value} hu
                LEFT JOIN {Tables.tickets.value} ht
                    ON ht.owner = hu.id
                WHERE ht.status = 4
            GROUP BY hu.id
        """
        return self.execute_select_all(sql)

    def tickets_get_by_user_id(self, user_id: int):
        sql = f"""
            SELECT ht.trackid, ht.status
            FROM {Tables.tickets.value} ht
                LEFT JOIN {Tables.users.value} hu
                    ON ht.owner = hu.id
                WHERE hu.id=%s AND hu.id != 1"""
        return self.execute_select_all(sql, params=(user_id))

    def tickets_by_email(self, email: str):
        # with self.connection.cursor() as cursor:
        sql = f"""
            SELECT ht.trackid, ht.subject, hu.name AS owner_name, hc.name AS category_name
            FROM {Tables.tickets.value} ht
                LEFT JOIN {Tables.users.value} hu
                    ON ht.owner = hu.id
                LEFT JOIN {Tables.categories.value} hc
                    ON ht.category = hc.id
                WHERE ht.email=%s AND ht.status != %s"""
        return self.execute_select_all(sql, (email, 3))
    
    def tickets_by_email_all(self, email: str):
        sql = f"""
            SELECT ht.trackid, ht.subject, hu.name AS owner_name, hc.name AS category_name
            FROM {Tables.tickets.value} ht
                LEFT JOIN {Tables.users.value} hu
                    ON ht.owner = hu.id
                LEFT JOIN {Tables.categories.value} hc
                    ON ht.category = hc.id
                WHERE ht.email=%s"""
        return self.execute_select_all(sql, (email))

    def tickets_by_email_owner(self, email: str):
        # with self.connection.cursor() as cursor:
        sql = f"""
            SELECT ht.trackid, ht.subject, hu.name AS owner_name, hc.name AS category_name
            FROM {Tables.tickets.value} ht
                LEFT JOIN {Tables.users.value} hu
                    ON ht.owner = hu.id
                LEFT JOIN {Tables.categories.value} hc
                    ON ht.category = hc.id
                WHERE hu.email=%s AND ht.status != %s"""
            # cursor.execute(sql, (email, 3))
            # result = cursor.fetchall()
            # return result
        return self.execute_select_all(sql, (email, 3))

    def ticket_get(self, ticket_id: int):
        # with self.connection.cursor() as cursor:
        sql = f"""
            SELECT ht.*, hu.name AS owner_name, hc.name AS category_name
            FROM {Tables.tickets.value} ht
                LEFT JOIN {Tables.users.value} hu
                    ON ht.owner = hu.id
                LEFT JOIN {Tables.categories.value} hc
                    ON ht.category = hc.id
                WHERE ht.id=%s
                LIMIT 1"""
        # cursor.execute(sql, (ticket_id))
        result = self.execute_select_one(sql, (ticket_id))
        if result:
            result["status"] = self.ticket_status_get(result["status"])
            result["notes"] = self.notes_get_by_ticket_id(result.get('id'))
        return result
    
    def ticket_get_by_track_id(self, track_id: str):
        sql = f"""
            SELECT ht.*, hu.name AS owner_name, hc.name AS category_name
            FROM {Tables.tickets.value} ht
                LEFT JOIN {Tables.users.value} hu
                    ON ht.owner = hu.id
                LEFT JOIN {Tables.categories.value} hc
                    ON ht.category = hc.id
                WHERE ht.trackid=%s
                LIMIT 1"""
        result = self.execute_select_one(sql, (track_id))
        if result:
            result["status"] = self.ticket_status_get(result["status"])
            result["notes"] = self.notes_get_by_ticket_id(result.get('id'))
        return result

    def tickets_get(self):
        sql = f"""SELECT * FROM {Tables.tickets.value}"""
        return self.execute_select_all(sql)

    def tickets_get_history_replies(self, ticket_trackid: str):
        sql = f"""
        SELECT hr.name, hr.message FROM {Tables.tickets.value} ht 
            LEFT JOIN {Tables.replies.value} hr
                ON ht.id = hr.replyto
            WHERE ht.trackid = %s"""
        return self.execute_select_all(sql, (ticket_trackid))
    
    def ticket_status_get(self, status_id: int):
        result = statuses.get(status_id)
        if not result:
            result = "Нет статуса"
            sql = f"""
                SELECT name FROM {Tables.custom_statutes.value}
                WHERE id=%s"""
            status = self.execute_select_one(sql, (status_id))
            if status:
                result = status.get('name')
        return result

    def ticket_status_update(self, trackid: str, new_status: str = "3"):
        sql = f"UPDATE {Tables.tickets.value} SET status=%s WHERE trackid=%s"
        self.execute_with_commit(sql, (new_status, trackid))

    def ticket_owner_update(self, trackid: str, new_owner_id: int):
        sql = f"UPDATE {Tables.tickets.value} SET owner=%s WHERE trackid=%s"
        self.execute_with_commit(sql, (new_owner_id, trackid))
        sql_2 = f"""
        SELECT hu.name,hu.email,hc.username FROM {Tables.users.value} hu
        LEFT JOIN  {Tables.clients.value} hc
            ON hu.email = hc.email
        WHERE hu.id=%s
        """
        return self.execute_select_one(sql_2, (new_owner_id))

    def ticket_get_custom_fields(self, ticket: dict):
        custom_fields_original = self.mapping_category2custom_flds(ticket.get("category"))
        # TODO
        log.debug(custom_fields_original)
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
                    cf['type'] = cfo['type']
        return cf_values_from_ticket


    def categories_get(self):
        # with self.connection.cursor() as cursor:
        sql = f"""SELECT * FROM {Tables.categories.value}"""
            # cursor.execute(sql)
            # result = cursor.fetchall()
            # return result
        return self.execute_select_all(sql)

    def category_get(self, category_id: int):
        # with self.connection.cursor() as cursor:
        sql = f"""SELECT * FROM {Tables.categories.value} WHERE id=%s"""
            # cursor.execute(sql, (category_id))
            # result = cursor.fetchone()
            # return result
        return self.execute_select_one(sql, (category_id))
        
    def custom_fields_get(self):
        # with self.connection.cursor() as cursor:
        sql = f"""SELECT * FROM {Tables.custom_fields.value}"""
            # cursor.execute(sql)
            # result = cursor.fetchall()
            # return result
        return self.execute_select_all(sql)
        
    def custom_field_get(self, custom_field_id):
        # with self.connection.cursor() as cursor:
        sql = f"""SELECT * FROM {Tables.custom_fields.value} WHERE id=%s"""
            # cursor.execute(sql, (custom_field_id))
            # result = cursor.fetchone()
            # return result
        return self.execute_select_one(sql, (custom_field_id))
    
    def mapping_category2custom_flds(self, category_id: int):
        # with self.connection.cursor() as cursor:
        sql = f"""SELECT * FROM {Tables.custom_fields.value} 
                    WHERE `use` > %s
                    ORDER BY id"""
        result = self.execute_select_all(sql, (1))
        payload = []
        if not result:
            return payload
        for row in result:
            category_list: list = []
            try:
                category_list = literal_eval(row.get('category'))
            except ValueError:
                category_list = ["*"]
            if str(category_id) in category_list:
                row["name"] = list(json.loads(row.get("name")).values())[0]
                row["value"] = json.loads(row.get("value"))
                payload.append(row)
            elif "*" in category_list:
                row["name"] = list(json.loads(row.get("name")).values())[0]
                row["value"] = json.loads(row.get("value"))
                payload.append(row)
        return payload
        
    def create_table_for_api(self):
        # with self.connection.cursor() as cursor:
        sql_script = f"""
            CREATE TABLE IF NOT EXISTS {Tables.clients.value} (
                id INT PRIMARY KEY AUTO_INCREMENT,
                telegram_id BIGINT NOT NULL UNIQUE,
                email VARCHAR(50) NOT NULL UNIQUE,
                isadmin BOOLEAN DEFAULT false,
                username VARCHAR(50),
                fio VARCHAR(50),
                isnotify BOOLEAN DEFAULT false
            );
            """
        log.debug(f"CREATE TABLE IF NOT EXISTS [{Tables.clients.value}]")
        return self.execute_with_commit(sql_script)
    
    def client_get_by_tid(self, telegram_id: int):
        # with self.connection.cursor() as cursor:
        sql = f"""SELECT * FROM {Tables.clients.value} WHERE telegram_id=%s"""
            # cursor.execute(sql, (telegram_id))
            # result = cursor.fetchone()
            # return result
        return self.execute_select_one(sql, (telegram_id))
    
    def client_create(self, telegram_id: int, email: str, fio: str, username: str = None):
        # result = None
        # with self.connection.cursor() as cursor:
        sql = f"""INSERT INTO {Tables.clients.value} (telegram_id, email, username, fio) VALUES (%s, %s, %s, %s)"""
            # try:
            #     cursor.execute(sql, (telegram_id, email, username, fio))
            #     self.connection.commit()
            # except IntegrityError as err:
            #     result = err.args[-1]
        self.execute_with_commit(sql, (telegram_id, email, username, fio))
        # return result
    
    def client_delete(self, telegram_id: int):
        # result = None
        # with self.connection.cursor() as cursor:
        sql = f"""DELETE FROM {Tables.clients.value} WHERE telegram_id=%s"""
            # try:
            #     cursor.execute(sql, (telegram_id))
            #     self.connection.commit()
            # except IntegrityError as err:
            #     result = {"error" : err.args[-1]}
        # return result
        self.execute_with_commit(sql, (telegram_id))
    
    def client_reload(self, telegram_id: int):
        result = None
        # with self.connection.cursor() as cursor:
        is_admin = False
        sql_select = f"""SELECT COUNT(*) as exist FROM {Tables.users.value} hu
                    LEFT JOIN {Tables.clients.value} hc 
                        ON hu.email = hc.email 
                        WHERE hc.telegram_id = %s"""
        sql_update = f"""UPDATE {Tables.clients.value} SET isadmin=%s WHERE telegram_id=%s"""
        result = self.execute_select_one(sql_select, (telegram_id))
        # cursor.execute(sql_select, (telegram_id))
        # result = cursor.fetchone()
        if result:
            is_admin = result.get("exist")
            # cursor.execute(sql_update, (is_admin, telegram_id))
            # self.connection.commit()        
            self.execute_with_commit(sql_update, (is_admin, telegram_id))            
        # except IntegrityError as err:
        #     result = {"error" : err.args[-1]}
        return result
    
    def kb_categories_get(self):
        sql = f"""SELECT id,name,parent,articles,articles_private,type FROM {Tables.kb_categories.value}"""
        kb_categories = self.execute_select_all(sql)
        log.debug(kb_categories)
        if not kb_categories:
            return []
        return kb_categories
        # max_deep: dict = max(kb_categories, key=lambda x: x['parent'])
        # categories = []
        # for i in range(1, max_deep.get('parent')+1):
        #     buff = []
        #     for c in kb_categories:
        #         if i == c.get('parent'):
        #             buff.append(c)
        #     categories.append(buff)
        # return categories
    def kb_articles_get(self):
        sql = f"""SELECT id,catid,subject,type FROM {Tables.kb_articles.value}"""
        kb_articles = self.execute_select_all(sql)
        log.debug(kb_articles)
        if not kb_articles:
            return []
        return kb_articles
    
    def kb_article_content_get(self, artid: int):
        sql = f"""SELECT subject,content from {Tables.kb_articles.value} WHERE id=%s"""
        content = self.execute_select_one(sql, artid)
        return content
    
    def notes_get_by_ticket_id(self, ticket_id: int):
        sql = f"""
        SELECT hu.name, hn.message FROM {Tables.notes.value} hn
            LEFT JOIN hesk_users hu
    	        ON hu.id=hn.who
            WHERE ticket=%s
        """
        return self.execute_select_all(sql, (ticket_id))
    
    def notes_create_note(self, ticket_id: int, message: str, email_from: str = None):
        id_from = None
        if email_from:
            id_from = self.execute_select_one(
                f"SELECT id FROM {Tables.users.value} WHERE email=%s", 
                email_from)
        if id_from:
            id_from = id_from.get('id')
        else:
            id_from = 1
        sql = f"""
        INSERT INTO {Tables.notes.value} (ticket,message,who,attachments) 
            VALUES (%s,%s,%s,"")
        """
        return self.execute_with_commit(sql, (ticket_id, message, id_from))
    
    def find_all_attachments_by_ticket_id(self, ticket_id: int | str):
        if type(ticket_id) == str:
            ticket = self.ticket_get_by_track_id(ticket_id)
            if ticket:
                ticket_id = ticket.get('id')
        sql_ticket = f"""
        SELECT attachments FROM {Tables.tickets.value} ht WHERE ht.id=%s
        UNION
        SELECT attachments FROM {Tables.replies.value} ha WHERE ha.replyto=%s
        """
        att_rows = self.execute_select_all(sql_ticket, (ticket_id, ticket_id))
        payload = []
        if att_rows:
            for row in att_rows:
                if row:
                    for attr in row.get('attachments').split(','):
                        _attr: str = attr.split('#')[0]
                        if _attr.isdigit() and _attr:
                            payload.append(int(attr.split('#')[0]))
        return payload

    
    def attachments_get_info(self, att_ids=()):
        sql = f"SELECT * FROM {Tables.attachments.value}"
        if att_ids:
            att_ids_format = ','.join('%s' for _ in att_ids)
            sql += f" WHERE att_id IN ({att_ids_format})"
        return self.execute_select_all(sql, (att_ids))