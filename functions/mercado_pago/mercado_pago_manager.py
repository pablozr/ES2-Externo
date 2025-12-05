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

    async def realiza_pagamento(self, cartao: dict, valor: float) -> dict:
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

            token = sdk.card_token().create(card_data)

            if token["status"] != 201:
                return{"status": False, "mensagem": "Dados invalidos"}

            token_id = token["response"]["id"]

            payment_data = {
                "transaction_amount": float(valor),
                "token": token_id,
                "description": "Cobranca",
                "installments": 1,

                "payer": {
                    "email": "ciclista.brasileiro@teste.com",
                }
            }

            payment = sdk.payment().create(payment_data)

            if payment["response"]["status"] == "approved":
                return{"status": True}
            else:
                return {"status": False, "mensagem": payment["response"]}

        except Exception as e:
            print(e)
            return {"status": False, "mensagem": "Erro interno"}


mercado_pago_instance = MercadoPagoManager()