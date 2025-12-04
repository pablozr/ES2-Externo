import os
from dotenv import load_dotenv
import mercadopago

load_dotenv()
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))


class MercadoPagoManager:

    async def valida_cartao(self, cartao: dict) -> dict:
        try:
            exp_month = cartao["validade"].split("-")[1]
            exp_year = cartao["validade"].split("-")[0]
            card_number = cartao["numero"].replace(" ", "")

            card_data = {
                "card_number": card_number,
                "expiration_month": int(exp_month),
                "expiration_year": int(exp_year),
                "security_code": cartao["cvv"],
                "cardholder": {
                    "name": cartao["nomeTitular"],
                },
            }

            result = sdk.card_token().create(card_data)

            if result["status"] != 201:
                return {"codigo": 422, "mensagem": "Dados Inválidos"}
            else:
                return {"status": True, "mensagem": "Cartão válido"}

        except Exception as e:
            print(e)
            return {"status": False, "mensagem": "Erro ao validar o cartão de crédito"}


mercado_pago_instance = MercadoPagoManager()