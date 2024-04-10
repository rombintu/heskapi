from sys import exit

from core.store import Store, StoreCreds
from core.service_api import Ticket, Message_from_hesk, create_new_ticket
from core.config import Config
from core import bot_api
from core import post_api
from utils.logger import logger as log
from fastapi import FastAPI

Config.check_empty()

store = Store(StoreCreds(
    Config.mysql_host, Config.mysql_user, 
    Config.mysql_pass, Config.mysql_database,
))

app = FastAPI()

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users",
    },
    {
        "name": "tickets",
        "description": "Manage tickets",
    },
    {
        "name": "categories",
        "description": "Manage categories",
    },
    {
        "name": "custom_fields",
        "description": "Manage custom_fields",
    },
    {
        "name": "email",
        "description": "Manage email",
    },
]

@app.get("/")
def root():
    return store.check_version()

@app.get("/users", tags=['users'])
async def users_get():
    return store.users_get()

@app.get("/users/{user_id}", tags=['users'])
async def users_get_by_id(user_id: int):
    return store.user_get(user_id)

@app.get("/tickets", tags=['tickets'])
async def tickets_get():
    return store.tickets_get()

@app.get("/tickets/{ticket_id}", tags=['tickets'])
async def tickets_get_by_id(ticket_id: int):
    return store.ticket_get(ticket_id)

@app.get("/tickets/get", tags=['tickets'])
async def ticket_get_by_track_id(track: str):
    return store.ticket_get_by_track_id(track)

@app.get("/tickets/user/{user_id}", tags=['tickets'])
async def users_get_tickets_owner_without_status(user_id: int, skip_status_id: int = 3):
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
    return store.tickets_user_owner_without_status(user_id, skip_status_id)

@app.post("/tickets", tags=["tickets"])
async def tickets_create(ticket: Ticket):
    status = create_new_ticket(ticket)
    return {"payload": ticket, "status": status}

@app.post("/tickets/notify", tags=["tickets"])
async def tickets_notify(mess_unparsed: Message_from_hesk):
    track_id = mess_unparsed.ticket_trackid
    chat_ids = mess_unparsed.chat_ids
    if not chat_ids:
        return {"message": "chat_ids is empty, task canceled"}
    ticket = store.ticket_get_by_track_id(track_id)
    if not ticket:
        return {"message": f"ticket {track_id} not found"}
    custom_fields = store.ticket_get_custom_fields(ticket)
    message, btns = bot_api.build_message_for_ticket(ticket, custom_fields)
    payload = bot_api.bot_send_message(message, btns, chat_ids)
    log.debug(payload)
    return payload

@app.get("/categories", tags=['categories'])
async def categories_get():
    return store.categories_get()

@app.get("/categories/{category_id}", tags=['categories'])
async def categories_get_by_id(category_id: int):
    return store.category_get(category_id)

@app.get("/custom_fields", tags=['custom_fields'])
async def custom_fields_get():
    return store.custom_fields_get()

@app.get("/custom_fields/{custom_field_id}", tags=['custom_fields'])
async def custom_fields_get_by_id(custom_field_id: int):
    return store.custom_field_get(custom_field_id)

@app.get("/custom_fields/mapping/{category_id}", tags=['custom_fields'])
async def custom_fields_mapping_category(category_id: int):
    """Return all use custom_fileds in category"""
    return store.mapping_category2custom_flds(category_id)

@app.post("/email", tags=['email'])
async def email_postmail(mail: post_api.EmailBody):
    message = post_api.post_mail.build_postmail_message(
        subject=mail.subject,
        to_addr=mail.to_addr,
        body=mail.body
    )
    err = post_api.post_mail.send_email(
        to_addr=mail.to_addr,
        builded_message=message
    )
    return {"error": err}