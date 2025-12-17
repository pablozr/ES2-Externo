from fastapi import APIRouter
from starlette.responses import JSONResponse

from functions.database.asyncpg_manager import asyncpg_manager

router = APIRouter()

@router.post("/restaurarBanco")
async def restaurar_banco():
    try:
        response = await asyncpg_manager.restaurar_banco()

        if not response["status"]:
            return JSONResponse(status_code=500, content={"mensagem": response["mensagem"]})

        return JSONResponse(status_code=200, content={"mensagem": response["mensagem"]})

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"mensagem": "Erro interno do servidor"})

