from json import dumps, load, loads
from core import store, api
from utils.logger import logger as log
from core.service_api import Ticket, ReplyPost
from core.bot_api import build_message_for_ticket, bot_send_message
import pytest
from core.post_api import PostMail, post_mail

def to_json(data):
    return dumps(data, indent=4, ensure_ascii=False, default=str)

def test_conn_database():
    version = store.check_version()
    log.debug(to_json(version))
    assert version[0].get("VERSION()") == "8.3.0"
    
def test_get_users():
    users = store.users_get()
    log.debug(to_json(users))
    assert len(users) > 0

def test_get_ticket_by_id():
    result = store.ticket_get_by_track_id("76B-DX6-RX1R")
    log.debug(to_json(result))
    # log.debug(result)
    assert len(result) > 0

def test_get_categories():
    result = store.categories_get()
    log.debug(to_json(result))

def test_get_category():
    result = store.category_get(1)
    log.debug(to_json(result))

def test_get_cfs():
    result = store.custom_fields_get()
    log.debug(to_json(result))

def test_get_cf_by_id():
    result = store.custom_field_get(1)
    log.debug(to_json(result))

def test_get_tickets_owner():
    result = store.tickets_user_owner_without_status(2)
    log.debug(to_json(result))

def test_mapping_cat2cfs():
    result = store.mapping_category2custom_flds(1)
    log.debug(to_json(result))

def test_ticket_get_cf():
    ticket = store.ticket_get_by_track_id("5U6-B86-XPRS")
    result = store.ticket_get_custom_fields(ticket)
    log.debug(result)

def test_build_message():
    ticket = store.ticket_get_by_track_id("W4B-8RY-S7M8")
    cfs = store.ticket_get_custom_fields(ticket)
    result = build_message_for_ticket(ticket, cfs)
    log.debug(result)

def test_bot_send_message():
    ticket = store.ticket_get_by_track_id("YTJ-8RL-RE19")
    cfs = store.ticket_get_custom_fields(ticket)
    message, btns = build_message_for_ticket(ticket, cfs)
    result = bot_send_message(message, btns, "469973030")
    log.debug(result)

@pytest.mark.asyncio
async def test_create_ticket():
    # custom_fields = store.mapping_category2custom_flds(2)
    # log.debug(to_json(custom_fields))
    # cfs_names = []
    # for cf in custom_fields:
    #     cfs_names.append(f'custom{cf.get("id")}')
    # log.debug(to_json(cfs_names))
    ticket = Ticket(
        name="Name Lastname",
        email="cloudesk_at@at-consulting.ru",
        subject="ticket autocreate from testing",
        message="Тело письма", category=1, 
        custom_fields={} 
    )
    res = await api.tickets_create(ticket)
    log.debug(to_json(res))

def test_send_postmail():
    postmail = PostMail()

    message = postmail.build_postmail_message("testing", 'Hello world', 'rnikolskiy@at-consulting.ru')
    postmail.send_email('rnikolskiy@at-consulting.ru', message)

def test_client_create():
    result = store.client_create(11, "email@gmail.com", "testing")
    log.debug(result)

def test_kb_categories_get():
    result = store.kb_categories_get()
    log.debug(result)

def test_attachments_get():
    data = store.attachments_get_info([3,2])
    log.debug(data)

def test_attachments_find_attr():
    data = store.find_all_attachments_by_ticket_id(50)
    log.debug(data)

@pytest.mark.asyncio
async def test_reply_add():
    await api.replies_add(
        57, message=ReplyPost(reply_name="rsegsgse", content="f2g232323g")
    )

# @pytest.mark.asyncio
# async def test_check_new_emails():
#     await post_mail.check_new_emails(login_from=None)