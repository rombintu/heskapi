from core.store import Store, StoreCreds, Client
from core.service_api import Ticket, Message_from_hesk, NotePost, create_new_ticket
from core.config import Config, statuses
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
    {
        "name": "clients",
        "description": "Manage clients (custom table)",
    },
    {
        "name": "kb",
        "description": "Manage Knowledgebase",
    },
    {
        "name": "notes",
        "description": "Manage notes",
    }
]


@app.get("/")
def root():
    return store.check_version()

@app.get("/users", tags=['users'])
async def users_get(workloaded: bool = False):
    if workloaded:
        return store.users_get_workloaded()
    return store.users_get()

@app.get("/users/{user_id}", tags=['users'])
async def users_get_by_id(user_id: int):
    return store.user_get(user_id)

@app.get("/tickets", tags=['tickets'])
async def tickets_get(
    track: str = None, 
    email: str = None,
    admin_email: str = None,
    all: bool = False
    ):
    data = None
    if track:
        ticket = store.ticket_get_by_track_id(track)
        if not ticket:
            return data
        else:
            ticket_cf = store.ticket_get_custom_fields(ticket)
            ticket['custom_fields'] = ticket_cf
            data = ticket
    elif email:
        if all:
            data = store.tickets_by_email_all(email)
        data = store.tickets_by_email(email)
    elif admin_email:
        data = store.tickets_by_email_owner(admin_email)
    else:
        data = store.tickets_get()
    
    if type(data) == list:
        log.debug(f"COUNT RESULT: {len(data)}")
    else: 
        log.debug(data)
    return data

@app.get("/tickets/{ticket_id}", tags=['tickets'])
async def tickets_get_by_id(ticket_id: int):
    return store.ticket_get(ticket_id)
   

# @app.get("/tickets/get", tags=['tickets'])
# async def ticket_get_by_email(email: str):
#     return store.tickets_by_email(email)

@app.get("/tickets/user/{user_id}", tags=['tickets'])
async def tickets_get_by_user_id(user_id: int):
    return store.tickets_get_by_user_id(user_id)

@app.get("/tickets/{track}/replies", tags=['tickets'])
async def tickets_get_replies(track: str):
    return store.tickets_get_history_replies(track)

@app.put("/tickets/{track}/status/{new}", tags=['tickets'])
async def tickets_set_new_status(track: str, new: int = 3):
    if statuses.get(new):
        store.ticket_status_update(track, str(new))
        if new == 3:
            ticket = store.ticket_get_by_track_id(track)
            if not ticket:
                return
            m_body = post_api.templates['ticket_close'].format(
                name=ticket.get('name'),
                subject=ticket.get('subject'),
                trackid=ticket.get('trackid'),
                site_url=Config.hesk_web_url
            )
            message = post_api.post_mail.build_postmail_message(
                subject=ticket.get('subject'),
                body=m_body,
                to_addr=ticket.get('email')
            )
            err = post_api.post_mail.send_email(ticket.get('email'), message)
            log.debug(err)
    return

@app.put("/tickets/{track}/owner/{new}", tags=['tickets'])
async def tickets_set_new_status(track: str, new: int):
    store.ticket_owner_update(track, str(new))
    return

@app.post("/tickets", tags=["tickets"])
async def tickets_create(ticket: Ticket):
    log.debug(ticket)
    # TODO
    create_new_ticket(ticket)
    return {"ticket": ticket, "status": 200}

@app.post("/tickets/notify", tags=["tickets"])
async def tickets_notify(mess_unparsed: Message_from_hesk):
    track_id: str = mess_unparsed.ticket_trackid
    chat_ids: list = mess_unparsed.chat_ids

    log.debug(f"TICKET >> {track_id} CHATIDS >> {chat_ids}")
    if not chat_ids:
        return {"ok": False, "message": "chat_ids is empty, task canceled"}
    ticket = store.ticket_get_by_track_id(track_id)
    if not ticket:
        return {"ok": False, "message": f"ticket {track_id} not found"}
    custom_fields = store.ticket_get_custom_fields(ticket)
    message, btns = bot_api.build_message_for_ticket(ticket, custom_fields)
    log.debug(message)
    payload = bot_api.bot_notify(message, btns, chat_ids)
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
        body=mail.body,
        is_html=mail.is_html
    )
    err = post_api.post_mail.send_email(
        to_addr=mail.to_addr,
        builded_message=message
    )
    return {"error": err}

@app.get("/clients/{telegram_id}", tags=['clients'])
async def clients_get_by_telegram_id(telegram_id: int):
    return store.client_get_by_tid(telegram_id)

@app.get("/clients/reload/{telegram_id}", tags=['clients'])
async def clients_reload(telegram_id: int):
    error = store.client_reload(telegram_id)
    if error and error.get("error"):
        return error
    return store.client_get_by_tid(telegram_id)

@app.post("/clients/create", tags=['clients'])
async def clients_create(client: Client):
    return store.client_create(
        client.telegram_id, client.email, 
        client.fio, client.username)

@app.delete("/clients/{telegram_id}", tags=['clients'])
async def clients_delete(telegram_id: int):
    return store.client_delete(telegram_id)

@app.get("/kb/categories", tags=['kb'])
async def kb_categories_get():
    return store.kb_categories_get()

@app.get("/kb/articles", tags=['kb'])
async def kb_articles_get(artid: int = None):
    if not artid:
        return store.kb_articles_get()
    else:
        return store.kb_article_content_get(artid)

@app.get("/notes/{ticket_id}", tags=['notes'])
async def notes_get_by_ticketid(ticket_id: int):
    return store.notes_get_by_ticket_id(ticket_id)

@app.post("/notes/{ticket_id}", tags=['notes'])
async def notes_get_by_ticketid(ticket_id: int, message: NotePost):
    return store.notes_create_note(ticket_id, message.message, message.email_from)