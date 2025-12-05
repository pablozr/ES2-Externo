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

@router.get("/cobranca/{cobranca_id}")
async def get_cobranca(cobranca_id: int):
    try:
        response = await asyncpg_manager.get_cobranca_by_id(cobranca_id)

        if not response["status"]:
            return JSONResponse(status_code=404, content={"mensagem": response["mensagem"]})

        return JSONResponse(status_code=200, content=response["data"])

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"mensagem": "Erro interno do servidor"})