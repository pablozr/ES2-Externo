import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.cobranca.router import router


@pytest.fixture
def app():
    """Cria uma aplicação FastAPI para testes."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Cria um cliente de teste."""
    return TestClient(app)


class TestCobrancaRouter:
    """Testes para o router de cobrança."""

    def test_realiza_cobranca_sucesso(self, client):
        """Testa realização de cobrança com sucesso."""
        cobranca_data = {"valor": 100.00, "ciclista": 1}

        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.realizar_cobranca = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "FINALIZADA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": "2024-01-01T10:00:01",
                    "valor": 100.00,
                    "ciclista": 1
                }
            })

            response = client.post("/cobranca", json=cobranca_data)

            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_realiza_cobranca_falha(self, client):
        """Testa realização de cobrança com falha."""
        cobranca_data = {"valor": 100.00, "ciclista": 1}

        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.realizar_cobranca = AsyncMock(return_value={
                "status": False,
                "mensagem": "Ciclista não encontrado"
            })

            response = client.post("/cobranca", json=cobranca_data)

            assert response.status_code == 400

    def test_realiza_cobranca_erro_interno(self, client):
        """Testa realização de cobrança com erro interno."""
        cobranca_data = {"valor": 100.00, "ciclista": 1}

        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.realizar_cobranca = AsyncMock(side_effect=Exception("Erro"))

            response = client.post("/cobranca", json=cobranca_data)

            assert response.status_code == 500

    def test_realiza_cobranca_sem_valor(self, client):
        """Testa realização de cobrança sem valor."""
        cobranca_data = {"ciclista": 1}

        response = client.post("/cobranca", json=cobranca_data)

        assert response.status_code == 422

    def test_realiza_cobranca_sem_ciclista(self, client):
        """Testa realização de cobrança sem ciclista."""
        cobranca_data = {"valor": 100.00}

        response = client.post("/cobranca", json=cobranca_data)

        assert response.status_code == 422

    def test_get_cobranca_sucesso(self, client):
        """Testa busca de cobrança com sucesso."""
        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.get_cobranca_by_id = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "FINALIZADA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": "2024-01-01T10:00:01",
                    "valor": 100.00,
                    "ciclista": 1
                }
            })

            response = client.get("/cobranca/1")

            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_get_cobranca_nao_encontrada(self, client):
        """Testa busca de cobrança não encontrada."""
        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.get_cobranca_by_id = AsyncMock(return_value={
                "status": False,
                "mensagem": "Cobrança não encontrada"
            })

            response = client.get("/cobranca/999")

            assert response.status_code == 404
            assert "mensagem" in response.json()

    def test_get_cobranca_erro_interno(self, client):
        """Testa busca de cobrança com erro interno."""
        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.get_cobranca_by_id = AsyncMock(side_effect=Exception("Erro"))

            response = client.get("/cobranca/1")

            assert response.status_code == 500

    def test_get_cobranca_id_invalido(self, client):
        """Testa busca de cobrança com ID inválido."""
        response = client.get("/cobranca/abc")

        assert response.status_code == 422

    def test_colocar_cobranca_na_fila_sucesso(self, client):
        """Testa colocação de cobrança na fila com sucesso."""
        cobranca_data = {"valor": 100.00, "ciclista": 1}

        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.colocar_cobranca_na_fila = AsyncMock(return_value={
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

            response = client.post("/filaCobranca", json=cobranca_data)

            assert response.status_code == 200
            assert response.json()["status"] == "EM_FILA"

    def test_colocar_cobranca_na_fila_falha(self, client):
        """Testa colocação de cobrança na fila com falha."""
        cobranca_data = {"valor": 100.00, "ciclista": 1}

        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.colocar_cobranca_na_fila = AsyncMock(return_value={
                "status": False,
                "mensagem": "Ciclista não encontrado"
            })

            response = client.post("/filaCobranca", json=cobranca_data)

            assert response.status_code == 400

    def test_colocar_cobranca_na_fila_erro_interno(self, client):
        """Testa colocação de cobrança na fila com erro interno."""
        cobranca_data = {"valor": 100.00, "ciclista": 1}

        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.colocar_cobranca_na_fila = AsyncMock(side_effect=Exception("Erro"))

            response = client.post("/filaCobranca", json=cobranca_data)

            assert response.status_code == 500

    def test_processa_cobrancas_em_fila_sucesso(self, client):
        """Testa processamento de cobranças na fila com sucesso."""
        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.processar_fila_cobrancas = AsyncMock(return_value={
                "status": True,
                "data": [
                    {
                        "id": 1,
                        "status": "FINALIZADA",
                        "hora_solicitacao": "2024-01-01T10:00:00",
                        "hora_finalizacao": "2024-01-01T10:00:01",
                        "valor": 100.00,
                        "ciclista": 1
                    }
                ]
            })

            response = client.post("/processaCobrancasEmFila")

            assert response.status_code == 200
            assert len(response.json()) == 1

    def test_processa_cobrancas_em_fila_vazia(self, client):
        """Testa processamento de fila vazia."""
        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.processar_fila_cobrancas = AsyncMock(return_value={
                "status": True,
                "data": []
            })

            response = client.post("/processaCobrancasEmFila")

            assert response.status_code == 200
            assert response.json() == []

    def test_processa_cobrancas_em_fila_falha(self, client):
        """Testa processamento de fila com falha."""
        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.processar_fila_cobrancas = AsyncMock(return_value={
                "status": False,
                "mensagem": "Erro ao processar"
            })

            response = client.post("/processaCobrancasEmFila")

            assert response.status_code == 400

    def test_processa_cobrancas_em_fila_erro_interno(self, client):
        """Testa processamento de fila com erro interno."""
        with patch("routes.cobranca.router.asyncpg_manager") as mock_manager:
            mock_manager.processar_fila_cobrancas = AsyncMock(side_effect=Exception("Erro"))

            response = client.post("/processaCobrancasEmFila")

            assert response.status_code == 500

