import os
from typing import Optional

import asyncpg
from dotenv import load_dotenv

from functions.integration.ciclista_manager import ciclista_instance
from functions.mercado_pago.mercado_pago_manager import mercado_pago_instance

load_dotenv()

DB_URL = os.getenv("DB_URL")


class AsyncpgManager:
    def __init__(self):
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def connect(self):
        if self.pool is None:
            self.pool = await asyncpg.create_pool(dsn=DB_URL)

    async def disconnect(self):
        if self.pool is not None:
            await self.pool.close()

    async def realizar_cobranca(self, cobranca: dict) -> dict:
        cobranca_pendente_query = """
            INSERT INTO cobrancas(status, hora_solicitacao, hora_finalizacao, valor, ciclista)
                VALUES(
                      'PENDENTE',
                    NOW(),
                    NULL,
                    $1,
                    $2
                ) RETURNING id;
        """

        cobranca_finalizada_query = """
            UPDATE cobrancas
                SET status = 'FINALIZADA',
                    hora_finalizacao = NOW()
                WHERE id = $1
                RETURNING status, hora_solicitacao, hora_finalizacao, valor, ciclista, id;
        """

        cobranca_falha_query = """
            UPDATE cobrancas
                SET status           = 'FALHA', 
                    hora_finalizacao = NOW()
                WHERE id = $1; 
        """

        try:
            async with self.pool.acquire() as connection:
                cobranca_pendente_id = await connection.fetchval(cobranca_pendente_query, cobranca["valor"], cobranca["ciclista"])

            cartao = await ciclista_instance.obter_cartao(cobranca["ciclista"])
            if not cartao:
                return {"status": False, "mensagem": cartao["mensagem"]}
            print(f"DEBUG CARTAO: {cartao}")

            pagamento = await mercado_pago_instance.realiza_pagamento(cartao, cobranca["valor"])
            print(f"DEBUG PAGAMENTO: {pagamento}")

            if pagamento["status"]:
                async with self.pool.acquire() as connection:
                    cobranca_finalizada = await connection.fetchrow(cobranca_finalizada_query, cobranca_pendente_id)
                return {"status": True, "data": {**cobranca_finalizada}}
            else:
                async with self.pool.acquire() as connection:
                    await connection.execute(cobranca_falha_query, cobranca_pendente_id)
                return {"status": False, "mensagem": pagamento["mensagem"]}

        except Exception as e:
            print(e)
            async with self.pool.acquire() as connection:
                await connection.execute(cobranca_falha_query, cobranca_pendente_id)
            return {"status": False, "mensagem": "Erro ao processar a cobrança"}



asyncpg_manager  = AsyncpgManager()