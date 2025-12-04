from fastapi import APIRouter
from starlette.responses import JSONResponse

from entities.cartao.cartao import Cartao
from functions.stripe.mercado_pago_manager import mercado_pago_instance

router = APIRouter()

@router.post("/validaCartaoDeCredito")
async def valida_cartao(cartao: Cartao):
    cartao = cartao.model_dump()

    try:
        response = await mercado_pago_instance.valida_cartao(cartao)

        if not response["status"]:
            return JSONResponse(status_code=400, content={"codigo": 400, "mensagem": response["mensagem"]})

        return JSONResponse(status_code=200, content=response["mensagem"])

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"mensagem": "Erro interno do servidor"})