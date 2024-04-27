from os import getenv
from sys import exit
from dotenv import load_dotenv
from enum import Enum

# from core.store import StoreCreds
from utils.logger import logger as log

load_dotenv()

class Config:
    mysql_host = getenv("MYSQL_HOST")
    mysql_user = getenv("MYSQL_USER")
    mysql_pass = getenv("MYSQL_PASS")
    mysql_database = getenv("MYSQL_DATABASE")
    mysql_table_prefix = getenv("MYSQL_TABLE_PREFIX", "hesk_")

    hesk_web_url = getenv("HESK_WEB_URL")

    bot_token = getenv("BOT_TOKEN")
    bot_url = "https://api.telegram.org/bot"

    smtp_login = getenv("SMTP_LOGIN")
    smtp_sender = getenv("SMTP_SENDER")
    smtp_password = getenv("SMTP_PASSWORD")
    smtp_host = getenv("SMTP_HOST")
    smtp_port = getenv("SMTP_PORT", 587)

    @classmethod
    def check_empty(cls):
        empty_values = []
        for k, v in cls.__dict__.items():
            if k == "__doc__":
                continue
            if not v:
                empty_values.append(k.upper())
        if empty_values:
            log.warning(f"Some empty var in ENV: {', '.join(empty_values)}")
        return not empty_values
    
class Tables(Enum):
    
    users = Config.mysql_table_prefix + "users"
    categories = Config.mysql_table_prefix + "categories"
    tickets = Config.mysql_table_prefix + "tickets"
    custom_statutes = Config.mysql_table_prefix + "custom_statuses"
    custom_fields = Config.mysql_table_prefix + "custom_fields"
    clients = Config.mysql_table_prefix + "clients"
    replies = Config.mysql_table_prefix + "replies"


statuses = {
    0: "Новая",
    1: "Получен комментарий",
    2: "Комментарий отправлен",
    3: "Решена",
    4: "В работе",
    5: "Приостановлена",
}