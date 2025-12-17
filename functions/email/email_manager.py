import random

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, MessageSchema, FastMail, MessageType
import os

from pydantic import SecretStr
from pydantic.v1 import EmailStr

load_dotenv()


class EmailManager:
    def __init__(self):
        self.config = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=SecretStr(os.getenv("MAIL_PASSWORD")),
            MAIL_FROM=EmailStr(os.getenv("MAIL_FROM")),
            MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
            MAIL_SERVER=os.getenv("MAIL_SERVER"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )

    async def send_email(self, email_data: dict) -> dict:
        try:
            message = MessageSchema(
                subject=email_data["assunto"],
                recipients=[email_data["email"]],
                body=email_data["mensagem"],
                subtype=MessageType.html,
            )

            fm = FastMail(self.config)
            await fm.send_message(message)

            record = {
                "id": random.randint(1, 1000),
                "email": email_data["email"],
                "assunto": email_data["assunto"],
                "mensagem": email_data["mensagem"],
            }

            return {"status": True, "data": record}

        except Exception as e:
            print(e)
            return {"codigo": 404, "mensagem": "Email não encontrado"}


email_instance = EmailManager()