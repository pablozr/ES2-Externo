"""
Testes de integração para a API de cobrança.
Testa o fluxo completo de cobrança através da API.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.cobranca.router import router


class MockAsyncContextManager:
    """Helper para simular async context manager."""
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def app():
    """Cria aplicação FastAPI para testes de integração."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Cliente de teste."""
    return TestClient(app)


@pytest.fixture
def mock_db_connection():
    """Mock para conexão do banco de dados."""
    pool = MagicMock()
    connection = AsyncMock()
    pool.acquire.return_value = MockAsyncContextManager(connection)
    pool.close = AsyncMock()
    return pool, connection


class TestCobrancaIntegration:
    """Testes de integração para cobranças."""

    def test_fluxo_completo_cobranca_aprovada(self, client, sample_cobranca, mock_db_connection):
        """
        Testa o fluxo completo de uma cobrança aprovada.
        
        Cenário: Ciclista faz aluguel, sistema cobra valor no cartão
        Resultado esperado: Cobrança criada e finalizada com sucesso
        """
        pool, connection = mock_db_connection
        
        # Configurar mocks
        connection.fetchval.return_value = 1  # ID da cobrança
        connection.fetchrow.return_value = {
            "id": 1,
            "status": "FINALIZADA",
            "hora_solicitacao": datetime.now(),
            "hora_finalizacao": datetime.now(),
            "valor": 100.00,
            "ciclista": 1
        }

        cartao_data = {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.realizar_cobranca = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "FINALIZADA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": "2024-01-01T10:00:05",
                    "valor": 100.00,
                    "ciclista": 1
                }
            })

            response = client.post("/cobranca", json=sample_cobranca)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "FINALIZADA"
            assert data["valor"] == 100.00
            assert data["ciclista"] == 1

    def test_fluxo_completo_cobranca_rejeitada(self, client, sample_cobranca):
        """
        Testa o fluxo de cobrança quando o pagamento é rejeitado.
        
        Cenário: Cartão sem limite ou bloqueado
        Resultado esperado: Cobrança falha com mensagem apropriada
        """
        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.realizar_cobranca = AsyncMock(return_value={
                "status": False,
                "mensagem": "Pagamento rejeitado: saldo insuficiente"
            })

            response = client.post("/cobranca", json=sample_cobranca)

            assert response.status_code == 400

    def test_fluxo_cobranca_ciclista_inexistente(self, client):
        """
        Testa cobrança para ciclista que não existe.
        
        Cenário: Sistema tenta cobrar ciclista não cadastrado
        Resultado esperado: Erro indicando ciclista não encontrado
        """
        cobranca = {"valor": 50.00, "ciclista": 99999}

        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.realizar_cobranca = AsyncMock(return_value={
                "status": False,
                "mensagem": "Ciclista não encontrado"
            })

            response = client.post("/cobranca", json=cobranca)

            assert response.status_code == 400

    def test_fluxo_consulta_cobranca_existente(self, client):
        """
        Testa consulta de cobrança existente.
        
        Cenário: Consultar detalhes de uma cobrança já realizada
        """
        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.get_cobranca_by_id = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "FINALIZADA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": "2024-01-01T10:00:05",
                    "valor": 100.00,
                    "ciclista": 1
                }
            })

            response = client.get("/cobranca/1")

            assert response.status_code == 200
            assert response.json()["id"] == 1
            assert response.json()["status"] == "FINALIZADA"

    def test_fluxo_consulta_cobranca_inexistente(self, client):
        """
        Testa consulta de cobrança que não existe.
        """
        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.get_cobranca_by_id = AsyncMock(return_value={
                "status": False,
                "mensagem": "Cobrança não encontrada"
            })

            response = client.get("/cobranca/99999")

            assert response.status_code == 404
            assert "mensagem" in response.json()

    def test_fluxo_fila_cobranca_sucesso(self, client, sample_cobranca):
        """
        Testa colocação de cobrança na fila para processamento posterior.
        
        Cenário: Sistema coloca cobrança na fila durante horário de pico
        """
        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.colocar_cobranca_na_fila = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "EM_FILA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": None,
                    "valor": 100.00,
                    "ciclista": 1
                }
            })

            response = client.post("/filaCobranca", json=sample_cobranca)

            assert response.status_code == 200
            assert response.json()["status"] == "EM_FILA"

    def test_fluxo_processamento_fila(self, client):
        """
        Testa processamento da fila de cobranças.
        
        Cenário: Sistema processa todas as cobranças pendentes na fila
        """
        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.processar_fila_cobrancas = AsyncMock(return_value={
                "status": True,
                "data": [
                    {
                        "id": 1,
                        "status": "FINALIZADA",
                        "hora_solicitacao": "2024-01-01T10:00:00",
                        "hora_finalizacao": "2024-01-01T10:05:00",
                        "valor": 100.00,
                        "ciclista": 1
                    },
                    {
                        "id": 2,
                        "status": "FINALIZADA",
                        "hora_solicitacao": "2024-01-01T10:01:00",
                        "hora_finalizacao": "2024-01-01T10:05:01",
                        "valor": 50.00,
                        "ciclista": 2
                    }
                ]
            })

            response = client.post("/processaCobrancasEmFila")

            assert response.status_code == 200
            assert len(response.json()) == 2
            assert all(c["status"] == "FINALIZADA" for c in response.json())

    def test_fluxo_processamento_fila_vazia(self, client):
        """
        Testa processamento quando não há cobranças na fila.
        """
        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.processar_fila_cobrancas = AsyncMock(return_value={
                "status": True,
                "data": []
            })

            response = client.post("/processaCobrancasEmFila")

            assert response.status_code == 200
            assert response.json() == []

    def test_fluxo_cobranca_valores_limite(self, client):
        """
        Testa cobranças com valores nos limites.
        
        Cenário: Valores muito pequenos e muito grandes
        """
        valores = [0.01, 0.50, 1.00, 100.00, 1000.00, 9999.99]

        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            for valor in valores:
                mock_asyncpg.realizar_cobranca = AsyncMock(return_value={
                    "status": True,
                    "data": {
                        "id": 1,
                        "status": "FINALIZADA",
                        "hora_solicitacao": "2024-01-01T10:00:00",
                        "hora_finalizacao": "2024-01-01T10:00:05",
                        "valor": valor,
                        "ciclista": 1
                    }
                })

                response = client.post("/cobranca", json={"valor": valor, "ciclista": 1})
                assert response.status_code == 200, f"Falhou para valor: {valor}"

    def test_fluxo_cobranca_concorrente(self, client, sample_cobranca):
        """
        Testa múltiplas cobranças em sequência (simula concorrência).
        """
        with patch("routes.cobranca.router.asyncpg_manager") as mock_asyncpg:
            mock_asyncpg.realizar_cobranca = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "FINALIZADA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": "2024-01-01T10:00:05",
                    "valor": 100.00,
                    "ciclista": 1
                }
            })

            resultados = []
            for i in range(5):
                cobranca = {"valor": 10.00 * (i + 1), "ciclista": i + 1}
                response = client.post("/cobranca", json=cobranca)
                resultados.append(response.status_code)

            assert all(status == 200 for status in resultados)
            assert mock_asyncpg.realizar_cobranca.call_count == 5

