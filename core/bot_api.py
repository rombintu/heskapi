import requests

from core.config import Config

def build_message_for_ticket(ticket: dict, custom_fields: list = []):
    track = ticket.get("trackid")
    name = ticket.get("name")
    subject = ticket.get("subject")
    message = ticket.get("message")
    owner = ticket.get("owner_name")
    status = ticket.get("status")
    if not owner:
        owner = "Не назначен"
    category = ticket.get("category_name")
    buff = ""
    if custom_fields:
        buff = "\nДополнительные поля:"
        for cf in custom_fields:
            if cf.get('value'):
                buff += f"\n - {cf.get('name')}: `{cf.get('value')}`"
    
    reply_markup = {
        "inline_keyboard": [
                [
                    {"text":"Подробнее 🖥", "url": f"{Config.hesk_web_url}/admin/admin_ticket.php?track={track}"}
                ]
            ]
    }

    message = f"""Был отправлен новый запрос в службу поддержки. 
Информация о заявке `{track}`:
Запрос создал(а): {name}
Тема заявки: *{subject}*
Категория заявки: *{category}* {buff}

Тело заявки:
```bash
{message}
```
Исполнитель: _{owner}_
Статус заявки: _{status}_
"""
    return message, reply_markup

def bot_send_message(message: str, reply_markup: dict, chat_id):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "chat_id": chat_id,
        "parse_mode": "Markdown",
        "text": message,
        "reply_markup": reply_markup,
        'disable_notification': False,
    }
    
    response = requests.post(f"{Config.bot_url}{Config.bot_token}/sendMessage", json=data, headers=headers)
    return response.json()

def bot_notify(message: str, reply_markup: dict, *chat_ids: str):
    payload = []
    if not chat_ids:
        return payload
    for c in chat_ids:
        payload.append(bot_send_message(message, reply_markup, c))
    return payload