from pydantic import BaseModel


class CobrancaRequest(BaseModel):
    valor: float
    ciclista: int