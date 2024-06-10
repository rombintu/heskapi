import smtplib, ssl
import imaplib
from aioimaplib import aioimaplib
from email import message_from_bytes
# from email import encoders
# from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import Config
from utils.logger import logger as log

from pydantic import BaseModel

templates = {
    "ticket_close": """Уважаемый(ая) {name},

Статус Вашей заявки "{subject}" был изменен на Решена/Закрыта.

Трек ID: {trackid}

Это сообщение отправлено автоматически. Пожалуйста, не отвечайте на него.
------------------------
{site_url}""",
    "ticket_reply": """Уважаемый(ая) {name},

От сотрудника службы техподдержки получен ответ на вашу заявку "{subject}".

Это сообщение отправлено автоматически. Пожалуйста, не отвечайте на него.
------------------------
{site_url}"""
}

class EmailBody(BaseModel):
    subject: str
    to_addr: str
    body: str
    is_html: bool = False


class PostMail:
    def __init__(self) -> None:
        self.host = Config.smtp_host
        self.port = Config.smtp_port
        self.login = Config.smtp_login
        self.password = Config.smtp_password
        # Create a secure SSL context
        self.context = ssl.create_default_context()

    @staticmethod
    def build_postmail_message(subject, body, to_addr, from_addr=Config.smtp_sender, is_html=False):
        message = MIMEMultipart()
        message["From"] = from_addr
        message["To"] = to_addr
        message["Subject"] = subject
        # message["Bcc"] = to_addr
        message.attach(MIMEText(body, "html" if is_html else "plain"))

        return message.as_string()

    def send_email(self, to_addr: str, builded_message: str, from_addr=Config.smtp_sender):
        
        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(self.host, self.port)
            server.ehlo() # Can be omitted
            server.starttls(context=self.context) # Secure the connection
            server.ehlo() # Can be omitted
            server.login(self.login, self.password)
            
            error = server.sendmail(from_addr, to_addr, builded_message)
            log.warning(f"Post send mail. Errors: {error}")
        except Exception as err:
            log.error(err)
            return err
        finally:
            server.quit()
        return 0
    
    # # TODO
    # async def check_new_emails(self, login_from: str):
    #     imap = imaplib.IMAP4_SSL(host=self.host, port=aioimaplib.IMAP4_SSL_PORT, ssl_context=self.context)
    #     # await imap.s
    #     imap.login(self.login, self.password)
    #     imap.select('inbox')

    #     typ, msgnums = None, None
    #     if login_from:
    #         typ, msgnums = imap.search('UTF-8', 'FROM', login_from)
    #     else:
    #         typ, msgnums = imap.search('UTF-8', 'UNSEEN')
    #     log.debug(typ)
    #     log.debug(msgnums)
    #     for num in msgnums[0].split():
    #         typ, msg_data = imap.fetch(num, 'BODY[HEADER]')
    #         raw_email = b''.join(msg_data[0][1])
    #         email_message = message_from_bytes(raw_email)
    #         log.debug(f"New message from {login_from}: {email_message}")
        
    #     imap.close()
    #     imap.logout()

post_mail = PostMail()

