import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from functions.database.asyncpg_manager import AsyncpgManager


class MockAsyncContextManager:
    """Helper class para simular async context manager."""
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class TestAsyncpgManager:
    """Testes para o AsyncpgManager."""

    @pytest.fixture
    def asyncpg_manager(self):
        """Instância do AsyncpgManager para testes."""
        manager = AsyncpgManager()
        return manager

    @pytest.fixture
    def mock_pool(self):
        """Mock para o pool de conexões."""
        pool = MagicMock()
        connection = AsyncMock()
        
        # Configurar o context manager para acquire
        pool.acquire.return_value = MockAsyncContextManager(connection)
        pool.close = AsyncMock()
        
        return pool, connection

    @pytest.fixture
    def cobranca_data(self):
        """Dados de cobrança para teste."""
        return {"valor": 100.00, "ciclista": 1}

    @pytest.fixture
    def cartao_data(self):
        """Dados de cartão para teste."""
        return {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

    @pytest.mark.asyncio
    async def test_connect(self, asyncpg_manager):
        """Testa conexão com o banco de dados."""
        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool

            await asyncpg_manager.connect()

            mock_create_pool.assert_called_once()
            assert asyncpg_manager.pool == mock_pool

    @pytest.mark.asyncio
    async def test_connect_ja_conectado(self, asyncpg_manager):
        """Testa que connect não cria novo pool se já conectado."""
        existing_pool = AsyncMock()
        asyncpg_manager.pool = existing_pool

        with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            await asyncpg_manager.connect()

            mock_create_pool.assert_not_called()
            assert asyncpg_manager.pool == existing_pool

    @pytest.mark.asyncio
    async def test_disconnect(self, asyncpg_manager, mock_pool):
        """Testa desconexão do banco de dados."""
        pool, _ = mock_pool
        asyncpg_manager.pool = pool

        await asyncpg_manager.disconnect()

        pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_sem_pool(self, asyncpg_manager):
        """Testa desconexão quando não há pool."""
        asyncpg_manager.pool = None

        # Não deve lançar exceção
        await asyncpg_manager.disconnect()

    @pytest.mark.asyncio
    async def test_realizar_cobranca_sucesso(self, asyncpg_manager, mock_pool, cobranca_data, cartao_data):
        """Testa realização de cobrança com sucesso."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        # Mock da consulta de inserção
        connection.fetchval.return_value = 1

        # Mock da consulta de finalização
        mock_row = {
            "id": 1,
            "status": "FINALIZADA",
            "hora_solicitacao": datetime.now(),
            "hora_finalizacao": datetime.now(),
            "valor": 100.00,
            "ciclista": 1
        }
        connection.fetchrow.return_value = mock_row

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": True, 
                "data": cartao_data
            })

            with patch("functions.database.asyncpg_manager.mercado_pago_instance") as mock_mp:
                mock_mp.realiza_pagamento = AsyncMock(return_value={"status": True})

                result = await asyncpg_manager.realizar_cobranca(cobranca_data)

                assert result["status"] is True
                assert "data" in result
                assert result["data"]["id"] == 1

    @pytest.mark.asyncio
    async def test_realizar_cobranca_cartao_nao_encontrado(self, asyncpg_manager, mock_pool, cobranca_data):
        """Testa cobrança quando cartão não é encontrado."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": False, 
                "mensagem": "Ciclista não encontrado"
            })

            result = await asyncpg_manager.realizar_cobranca(cobranca_data)

            assert result["status"] is False
            assert "Ciclista não encontrado" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_realizar_cobranca_pagamento_falhou(self, asyncpg_manager, mock_pool, cobranca_data, cartao_data):
        """Testa cobrança quando pagamento falha."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        connection.fetchval.return_value = 1

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": True, 
                "data": cartao_data
            })

            with patch("functions.database.asyncpg_manager.mercado_pago_instance") as mock_mp:
                mock_mp.realiza_pagamento = AsyncMock(return_value={
                    "status": False, 
                    "mensagem": "Pagamento rejeitado"
                })

                result = await asyncpg_manager.realizar_cobranca(cobranca_data)

                assert result["status"] is False
                assert "Pagamento rejeitado" in result["mensagem"]
                connection.execute.assert_called_once()  # Deve marcar como FALHA

    @pytest.mark.asyncio
    async def test_realizar_cobranca_excecao(self, asyncpg_manager, mock_pool, cobranca_data, cartao_data):
        """Testa cobrança quando ocorre exceção."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        connection.fetchval.return_value = 1

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": True, 
                "data": cartao_data
            })

            with patch("functions.database.asyncpg_manager.mercado_pago_instance") as mock_mp:
                mock_mp.realiza_pagamento = AsyncMock(side_effect=Exception("Erro inesperado"))

                result = await asyncpg_manager.realizar_cobranca(cobranca_data)

                assert result["status"] is False
                assert "Erro ao processar" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_get_cobranca_by_id_sucesso(self, asyncpg_manager, mock_pool):
        """Testa busca de cobrança por ID com sucesso."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        mock_row = {
            "id": 1,
            "status": "FINALIZADA",
            "hora_solicitacao": datetime.now(),
            "hora_finalizacao": datetime.now(),
            "valor": 100.00,
            "ciclista": 1
        }
        connection.fetchrow.return_value = mock_row

        result = await asyncpg_manager.get_cobranca_by_id(1)

        assert result["status"] is True
        assert result["data"]["id"] == 1

    @pytest.mark.asyncio
    async def test_get_cobranca_by_id_nao_encontrada(self, asyncpg_manager, mock_pool):
        """Testa busca de cobrança não encontrada."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        connection.fetchrow.return_value = None

        result = await asyncpg_manager.get_cobranca_by_id(999)

        assert result["status"] is False
        assert result["mensagem"] == "Cobrança não encontrada"

    @pytest.mark.asyncio
    async def test_get_cobranca_by_id_excecao(self, asyncpg_manager, mock_pool):
        """Testa busca de cobrança com exceção."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        connection.fetchrow.side_effect = Exception("Database error")

        result = await asyncpg_manager.get_cobranca_by_id(1)

        assert result["status"] is False
        assert "Erro ao buscar" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_colocar_cobranca_na_fila_sucesso(self, asyncpg_manager, mock_pool, cobranca_data, cartao_data):
        """Testa colocação de cobrança na fila com sucesso."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        mock_row = {
            "id": 1,
            "status": "EM_FILA",
            "hora_solicitacao": datetime.now(),
            "hora_finalizacao": None,
            "valor": 100.00,
            "ciclista": 1
        }
        connection.fetchrow.return_value = mock_row

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": True, 
                "data": cartao_data
            })

            result = await asyncpg_manager.colocar_cobranca_na_fila(cobranca_data)

            assert result["status"] is True
            assert result["data"]["status"] == "EM_FILA"

    @pytest.mark.asyncio
    async def test_colocar_cobranca_na_fila_cartao_nao_encontrado(self, asyncpg_manager, mock_pool, cobranca_data):
        """Testa fila quando cartão não é encontrado."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": False, 
                "mensagem": "Ciclista não encontrado"
            })

            result = await asyncpg_manager.colocar_cobranca_na_fila(cobranca_data)

            assert result["status"] is False
            assert "Ciclista não encontrado" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_colocar_cobranca_na_fila_excecao(self, asyncpg_manager, mock_pool, cobranca_data, cartao_data):
        """Testa fila quando ocorre exceção."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": True, 
                "data": cartao_data
            })
            connection.fetchrow.side_effect = Exception("Database error")

            result = await asyncpg_manager.colocar_cobranca_na_fila(cobranca_data)

            assert result["status"] is False
            assert "Erro ao colocar" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_processar_fila_cobrancas_sucesso(self, asyncpg_manager, mock_pool, cartao_data):
        """Testa processamento da fila com sucesso."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        # Mock das cobranças na fila
        mock_rows = [
            {"id": 1, "valor": 100.00, "ciclista": 1},
            {"id": 2, "valor": 50.00, "ciclista": 2}
        ]
        connection.fetch.return_value = mock_rows

        # Mock da cobrança finalizada
        mock_finalizada = {
            "id": 1,
            "status": "FINALIZADA",
            "hora_solicitacao": datetime.now(),
            "hora_finalizacao": datetime.now(),
            "valor": 100.00,
            "ciclista": 1
        }
        connection.fetchrow.return_value = mock_finalizada

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": True, 
                "data": cartao_data
            })

            with patch("functions.database.asyncpg_manager.mercado_pago_instance") as mock_mp:
                mock_mp.realiza_pagamento = AsyncMock(return_value={"status": True})

                result = await asyncpg_manager.processar_fila_cobrancas()

                assert result["status"] is True
                assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_processar_fila_cobrancas_vazia(self, asyncpg_manager, mock_pool):
        """Testa processamento de fila vazia."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        connection.fetch.return_value = []

        result = await asyncpg_manager.processar_fila_cobrancas()

        assert result["status"] is True
        assert result["data"] == []

    @pytest.mark.asyncio
    async def test_processar_fila_cobrancas_excecao(self, asyncpg_manager, mock_pool):
        """Testa processamento de fila com exceção."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        connection.fetch.side_effect = Exception("Database error")

        result = await asyncpg_manager.processar_fila_cobrancas()

        assert result["status"] is False
        assert "Erro ao processar" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_processar_fila_pagamento_falha(self, asyncpg_manager, mock_pool, cartao_data):
        """Testa processamento quando pagamento falha."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        mock_rows = [{"id": 1, "valor": 100.00, "ciclista": 1}]
        connection.fetch.return_value = mock_rows

        with patch("functions.database.asyncpg_manager.ciclista_instance") as mock_ciclista:
            mock_ciclista.obter_cartao = AsyncMock(return_value={
                "status": True, 
                "data": cartao_data
            })

            with patch("functions.database.asyncpg_manager.mercado_pago_instance") as mock_mp:
                mock_mp.realiza_pagamento = AsyncMock(return_value={
                    "status": False, 
                    "mensagem": "Rejeitado"
                })

                result = await asyncpg_manager.processar_fila_cobrancas()

                assert result["status"] is True
                assert result["data"] == []  # Nenhuma cobrança processada

    @pytest.mark.asyncio
    async def test_restaurar_banco_sucesso(self, asyncpg_manager, mock_pool):
        """Testa restauração do banco com sucesso."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        result = await asyncpg_manager.restaurar_banco()

        assert result["status"] is True
        assert result["mensagem"] == "Banco de dados restaurado com sucesso"
        connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_restaurar_banco_excecao(self, asyncpg_manager, mock_pool):
        """Testa restauração do banco com exceção."""
        pool, connection = mock_pool
        asyncpg_manager.pool = pool

        connection.execute.side_effect = Exception("Database error")

        result = await asyncpg_manager.restaurar_banco()

        assert result["status"] is False
        assert "Erro ao restaurar" in result["mensagem"]