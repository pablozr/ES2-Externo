from pydantic import BaseModel, Field


class Cartao(BaseModel):
    nomeTitular: str
    numero: str = Field(..., min_length=13, max_length=19)
    validade: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    cvv: str