import requests
from datetime import datetime
from core.config import Config
from utils.logger import logger as log


def if_type_is_date(row: dict):
    value: str = row.get('value')
    value = int(value) if value.isdigit() else None
    if not value: return value
    date = datetime.fromtimestamp(value)
    return date.strftime("%d-%m-%Y")

def build_message_for_ticket(t: dict, custom_fields: list):
    # status = statuses[t.get('status')]
    trackid = t.get('trackid')
    # body = '' if not t.get('message') else t['message'].split('<br')[0] + "..."
    custom_fields_data = ""
    if custom_fields:
        for cf in custom_fields:
            log.debug(cf)
            if '<br />' in cf.get('value'):
                new_val = ''
                for val in cf['value'].split('<br />'):
                    new_val += f'\n    - {val} ✅'
                cf['value'] = new_val
            value = if_type_is_date(cf) if cf.get('type') == 'date' else cf.get('value')
            custom_fields_data += f'''\n- {cf.get("name") }: <code>{value if value else "-"}</code>'''
    message = f"""Заявка <code>{trackid}</code> -> {t.get('status')}\
        \n👨‍💻 {t.get('name')} \
        \n📪 {t.get('email')} \
        \n🔬 Категория: {t.get('category_name')}\
        \nТема: <em>{'' if not t.get('subject') else t['subject']}</em>\
        \nДополнительные поля:\
        \n{'- Нет' if not custom_fields_data else custom_fields_data}"""
    reply_markup = {
        "inline_keyboard": [
                [
                    {"text": "Синхронизировать ⚙️", "callback_data": f"tickets_reload_{trackid}"}  
                ],
                [
                    {"text": "Скрыть ❌", "callback_data": f"tickets_hide"},
                    {"text":"Подробнее 🖥", "url": f"{Config.hesk_web_url}/admin/admin_ticket.php?track={trackid}"}
                ]
            ]
        }
    return message, reply_markup

def bot_send_message(message: str, reply_markup: dict, chat_id: int):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "chat_id": chat_id,
        "parse_mode": "html",
        "text": message,
        "reply_markup": reply_markup,
        'disable_notification': False,
    }
    
    response = requests.post(f"{Config.bot_url}{Config.bot_token}/sendMessage", json=data, headers=headers)
    return response.json()

def bot_notify(message: str, reply_markup: dict, chat_ids: list):
    payload = []
    if not chat_ids:
        return payload
    for c in chat_ids:
        c_payload = bot_send_message(message, reply_markup, c)
        if not c_payload.get('ok'):
            bot_send_message("Не получилось распарсить новую заявку", reply_markup, c)
        payload.append(c_payload)
    return payload