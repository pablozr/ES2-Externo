import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.email.router import router


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


class TestEmailRouter:
    """Testes para o router de email."""

    def test_send_email_sucesso(self, client):
        """Testa envio de email com sucesso."""
        email_data = {
            "email": "test@example.com",
            "assunto": "Teste",
            "mensagem": "Mensagem de teste"
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 123,
                    "email": "test@example.com",
                    "assunto": "Teste",
                    "mensagem": "Mensagem de teste"
                }
            })

            response = client.post("/enviarEmail", json=email_data)

            assert response.status_code == 200
            assert response.json()["email"] == "test@example.com"

    def test_send_email_falha(self, client):
        """Testa envio de email com falha."""
        email_data = {
            "email": "test@example.com",
            "assunto": "Teste",
            "mensagem": "Mensagem de teste"
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": False,
                "message": "Email não encontrado"
            })

            response = client.post("/enviarEmail", json=email_data)

            assert response.status_code == 404

    def test_send_email_erro_interno(self, client):
        """Testa envio de email com erro interno."""
        email_data = {
            "email": "test@example.com",
            "assunto": "Teste",
            "mensagem": "Mensagem de teste"
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(side_effect=Exception("Erro"))

            response = client.post("/enviarEmail", json=email_data)

            assert response.status_code == 500
            assert "message" in response.json()

    def test_send_email_email_invalido(self, client):
        """Testa envio de email com email inválido."""
        email_data = {
            "email": "invalid-email",
            "assunto": "Teste",
            "mensagem": "Mensagem de teste"
        }

        response = client.post("/enviarEmail", json=email_data)

        assert response.status_code == 422

    def test_send_email_sem_assunto(self, client):
        """Testa envio de email sem assunto."""
        email_data = {
            "email": "test@example.com",
            "mensagem": "Mensagem de teste"
        }

        response = client.post("/enviarEmail", json=email_data)

        assert response.status_code == 422

    def test_send_email_sem_mensagem(self, client):
        """Testa envio de email sem mensagem."""
        email_data = {
            "email": "test@example.com",
            "assunto": "Teste"
        }

        response = client.post("/enviarEmail", json=email_data)

        assert response.status_code == 422

    def test_send_email_sem_email(self, client):
        """Testa envio de email sem email."""
        email_data = {
            "assunto": "Teste",
            "mensagem": "Mensagem de teste"
        }

        response = client.post("/enviarEmail", json=email_data)

        assert response.status_code == 422

    def test_send_email_body_vazio(self, client):
        """Testa envio de email com body vazio."""
        response = client.post("/enviarEmail", json={})

        assert response.status_code == 422

    def test_send_email_sem_body(self, client):
        """Testa envio de email sem body."""
        response = client.post("/enviarEmail")

        assert response.status_code == 422

    def test_send_email_com_html(self, client):
        """Testa envio de email com conteúdo HTML."""
        email_data = {
            "email": "test@example.com",
            "assunto": "Teste HTML",
            "mensagem": "<h1>Título</h1><p>Parágrafo</p>"
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 123,
                    "email": "test@example.com",
                    "assunto": "Teste HTML",
                    "mensagem": "<h1>Título</h1><p>Parágrafo</p>"
                }
            })

            response = client.post("/enviarEmail", json=email_data)

            assert response.status_code == 200

    def test_send_email_assunto_longo(self, client):
        """Testa envio de email com assunto longo."""
        email_data = {
            "email": "test@example.com",
            "assunto": "A" * 500,
            "mensagem": "Mensagem"
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 123,
                    "email": "test@example.com",
                    "assunto": "A" * 500,
                    "mensagem": "Mensagem"
                }
            })

            response = client.post("/enviarEmail", json=email_data)

            assert response.status_code == 200

