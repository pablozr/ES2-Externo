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

        cobranca_pendente_id = None

        try:

            cartao = await ciclista_instance.obter_cartao(cobranca["ciclista"])
            if not cartao["status"]:
                return {"status": False, "mensagem": cartao["mensagem"]}
            print(f"DEBUG CARTAO: {cartao}")

            async with self.pool.acquire() as connection:
                cobranca_pendente_id = await connection.fetchval(cobranca_pendente_query, cobranca["valor"], cobranca["ciclista"])

                pagamento = await mercado_pago_instance.realiza_pagamento(cartao["data"], cobranca["valor"])
                print(f"DEBUG PAGAMENTO: {pagamento}")

                if pagamento["status"]:
                    cobranca_finalizada = await connection.fetchrow(cobranca_finalizada_query, cobranca_pendente_id)
                    return {"status": True, "data": {**cobranca_finalizada, "hora_solicitacao": cobranca_finalizada["hora_solicitacao"].isoformat() if cobranca_finalizada["hora_solicitacao"] else None,
                                                     "hora_finalizacao": cobranca_finalizada["hora_finalizacao"].isoformat() if cobranca_finalizada["hora_finalizacao"] else None,
                                                     "valor": float(cobranca_finalizada["valor"])}}
                else:
                    await connection.execute(cobranca_falha_query, cobranca_pendente_id)
                    return {"status": False, "mensagem": pagamento["mensagem"]}

        except Exception as e:
            print(e)
            if cobranca_pendente_id:
                async with self.pool.acquire() as connection:
                    await connection.execute(cobranca_falha_query, cobranca_pendente_id)
            return {"status": False, "mensagem": "Erro ao processar a cobrança"}

    async def get_cobranca_by_id(self, cobranca_id: int) -> dict:
        query = """
            SELECT id, status, hora_solicitacao, hora_finalizacao, valor, ciclista
            FROM cobrancas
            WHERE id = $1;
        """

        try:
            async with self.pool.acquire() as connection:
                cobranca = await connection.fetchrow(query, cobranca_id)

                if cobranca:
                    return {"status": True, "data": {**cobranca, "hora_solicitacao": cobranca["hora_solicitacao"].isoformat() if cobranca["hora_solicitacao"] else None,
                                                     "hora_finalizacao": cobranca["hora_finalizacao"].isoformat() if cobranca["hora_finalizacao"] else None,
                                                     "valor": float(cobranca["valor"])}}
                else:
                    return {"status": False, "mensagem": "Cobrança não encontrada"}

        except Exception as e:
            print(e)
            return {"status": False, "mensagem": "Erro ao buscar a cobrança"}

    async def colocar_cobranca_na_fila(self, cobranca: dict) -> dict:
        query = """
            INSERT INTO cobrancas(status, hora_solicitacao, hora_finalizacao, valor, ciclista)
                VALUES(
                      'EM_FILA',
                    NOW(),
                    NULL,
                    $1,
                    $2
                ) RETURNING id, status, hora_solicitacao, hora_finalizacao, valor, ciclista;
        """

        try:

            cartao = await ciclista_instance.obter_cartao(cobranca["ciclista"])
            if not cartao["status"]:
                return {"status": False, "mensagem": cartao["mensagem"]}
            print(f"DEBUG CARTAO: {cartao}")

            async with self.pool.acquire() as connection:
                cobranca = await connection.fetchrow(query, cobranca["valor"], cobranca["ciclista"])
                return {"status": True, "data": {**cobranca, "hora_solicitacao": cobranca["hora_solicitacao"].isoformat() if cobranca["hora_solicitacao"] else None,
                                                 "hora_finalizacao": cobranca["hora_finalizacao"].isoformat() if cobranca["hora_finalizacao"] else None,
                                                 "valor": float(cobranca["valor"])}}

        except Exception as e:
            print(e)
            return {"status": False, "mensagem": "Erro ao colocar a cobrança na fila"}


asyncpg_manager  = AsyncpgManager()