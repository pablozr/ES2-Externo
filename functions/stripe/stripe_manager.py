import os
import stripe
from dotenv import load_dotenv

load_dotenv()


class StripeManager:
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_API_KEY")

    async def valida_cartao(self, cartao: dict) -> dict:
        try:
            exp_month = cartao["validade"].split("-")[1]
            exp_year = cartao["validade"].split("-")[0]

            token = stripe.Token.create(
                card={
                    "number": cartao["numero"],
                    "exp_month": int(exp_month),
                    "exp_year": int(exp_year),
                    "cvc": cartao["cvv"],
                },
            )

            if token:
                return {"status": True, "mensagem": "Cartão de crédito válido"}
            else:
                return {"status": False, "mensagem": "Cartão de crédito inválido"}

        except Exception as e:
            print(e)
            return {"status": False, "mensagem": "Erro ao validar o cartão de crédito"}


stripe_instance = StripeManager()