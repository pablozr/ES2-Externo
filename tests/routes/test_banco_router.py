import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.banco.router import router


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


class TestBancoRouter:
    """Testes para o router de banco."""

    def test_restaurar_banco_sucesso(self, client):
        """Testa restauração do banco com sucesso."""
        with patch("routes.banco.router.asyncpg_manager") as mock_manager:
            mock_manager.restaurar_banco = AsyncMock(return_value={
                "status": True,
                "mensagem": "Banco de dados restaurado com sucesso"
            })

            response = client.post("/restaurarBanco")

            assert response.status_code == 200
            assert response.json()["mensagem"] == "Banco de dados restaurado com sucesso"

    def test_restaurar_banco_falha(self, client):
        """Testa restauração do banco com falha."""
        with patch("routes.banco.router.asyncpg_manager") as mock_manager:
            mock_manager.restaurar_banco = AsyncMock(return_value={
                "status": False,
                "mensagem": "Erro ao restaurar o banco de dados"
            })

            response = client.post("/restaurarBanco")

            assert response.status_code == 500
            assert "mensagem" in response.json()

    def test_restaurar_banco_erro_interno(self, client):
        """Testa restauração do banco com erro interno."""
        with patch("routes.banco.router.asyncpg_manager") as mock_manager:
            mock_manager.restaurar_banco = AsyncMock(side_effect=Exception("Erro"))

            response = client.post("/restaurarBanco")

            assert response.status_code == 500
            assert "mensagem" in response.json()

