import os
import httpx
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("CICLISTA_SERVICE_URL")


class CiclistaManager:
    async def obter_cartao(self, ciclista_id: int) -> dict:
        endpoint = f"{base_url}{ciclista_id}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(endpoint)

                if response.status_code == 200:
                    return {"status": True, "data": response.json()}
                else:
                    return {"status": False, "mensagem": "Ciclista não encontrado"}
            except httpx.RequestError as e:
                print(e)
                return {"status": False, "mensagem": "Erro ao conectar ao serviço de ciclistas"}


ciclista_instance = CiclistaManager()