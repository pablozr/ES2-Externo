from pydantic import BaseModel, EmailStr


class Email(BaseModel):
    id: int
    email: EmailStr
    assunto: str
    mensagem: str

class EmailRequest(BaseModel):
    email: EmailStr
    assunto: str
    mensagem: str