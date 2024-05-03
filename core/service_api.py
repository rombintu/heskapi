import requests, json
from os import path
from core.config import Config

from pydantic import BaseModel

actions = {
    "submit_ticket": 
        {
            "path": "submit_ticket.php", 
            "params": {"sumbit" : "1"},
        },
}

class Ticket(BaseModel):
    name: str
    email:str
    subject: str | None
    message: str
    category: int = 1
    custom_fields: dict = {}

    def to_dict(self):
        data = {
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "category": self.category,
        }
        for k, v in self.custom_fields.items():
            if "custom" in k:
                data[k] = v
        return data

class Message_from_hesk(BaseModel):
    ticket_trackid: str
    chat_ids: list | None

def create_new_ticket(ticket: Ticket):
    response = requests.post(
        path.join(Config.hesk_web_url, actions["submit_ticket"]["path"]), 
        params=actions["submit_ticket"]["params"],
        data=ticket.to_dict(),
        verify=False,
        )
    return response.status_code

def get_token():
    ...