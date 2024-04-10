import smtplib, ssl

# from email import encoders
# from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import Config
from utils.logger import logger as log

from pydantic import BaseModel

class EmailBody(BaseModel):
    subject: str
    to_addr: str
    body: str


class PostMail:
    def __init__(self) -> None:
        self.host = Config.smtp_host
        self.port = Config.smtp_port
        self.login = Config.smtp_login
        self.password = Config.smtp_password
        # Create a secure SSL context
        self.context = ssl.create_default_context()

    @staticmethod
    def build_postmail_message(subject, body, to_addr, from_addr=Config.smtp_sender):
        message = MIMEMultipart()
        message["From"] = from_addr
        message["To"] = to_addr
        message["Subject"] = subject
        # message["Bcc"] = to_addr
        message.attach(MIMEText(body, "plain"))

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

post_mail = PostMail()