from fastapi import APIRouter
from starlette.responses import JSONResponse

from entities.cobranca.cobranca import CobrancaRequest
from functions.database.asyncpg_manager import asyncpg_manager

router = APIRouter()
@router.post("/cobranca")
async def realiza_cobranca(cobranca: CobrancaRequest):
    cobranca = cobranca.model_dump()

    try:
        response = await asyncpg_manager.realizar_cobranca(cobranca)

        if not response["status"]:
            return JSONResponse(status_code=400, content=response["mensagem"])

        return JSONResponse(status_code=200, content=response["data"])

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"mensagem": "Erro interno do servidor"})