from fastapi import APIRouter
from starlette.responses import JSONResponse

from entities.email.email import EmailRequest
from functions.email.email_manager import email_instance

router = APIRouter()

@router.post("/enviarEmail")
async def sendEmail(email: EmailRequest):

    email = email.model_dump()

    try:
        response = await email_instance.send_email(email)

        if not response["status"]:
            return JSONResponse(status_code=404, content={"codigo": response["status"], "messagem": response["message"]})

        return JSONResponse(status_code=200, content=response["data"])

    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"message": "Erro interno do servidor"})
