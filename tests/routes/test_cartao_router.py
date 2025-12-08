import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.cartao.router import router


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


class TestCartaoRouter:
    """Testes para o router de cartão."""

    def test_valida_cartao_sucesso(self, client):
        """Testa validação de cartão com sucesso."""
        cartao_data = {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": True,
                "mensagem": "Cartão válido"
            })

            response = client.post("/validaCartaoDeCredito", json=cartao_data)

            assert response.status_code == 200
            assert response.json() == "Cartão válido"

    def test_valida_cartao_dados_invalidos(self, client):
        """Testa validação de cartão com dados inválidos."""
        cartao_data = {
            "nomeTitular": "João",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": False,
                "mensagem": "Dados Inválidos"
            })

            response = client.post("/validaCartaoDeCredito", json=cartao_data)

            assert response.status_code == 400
            assert response.json()["codigo"] == 400
            assert "mensagem" in response.json()

    def test_valida_cartao_erro_interno(self, client):
        """Testa validação de cartão com erro interno."""
        cartao_data = {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(side_effect=Exception("Erro"))

            response = client.post("/validaCartaoDeCredito", json=cartao_data)

            assert response.status_code == 500
            assert "mensagem" in response.json()

    def test_valida_cartao_numero_invalido(self, client):
        """Testa validação de cartão com número inválido (muito curto)."""
        cartao_data = {
            "nomeTitular": "APRO",
            "numero": "123",  # muito curto
            "validade": "2030-12-01",
            "cvv": "123"
        }

        response = client.post("/validaCartaoDeCredito", json=cartao_data)

        assert response.status_code == 422  # Validation error

    def test_valida_cartao_validade_formato_invalido(self, client):
        """Testa validação de cartão com formato de validade inválido."""
        cartao_data = {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "12/2030",  # formato inválido
            "cvv": "123"
        }

        response = client.post("/validaCartaoDeCredito", json=cartao_data)

        assert response.status_code == 422

    def test_valida_cartao_sem_cvv(self, client):
        """Testa validação de cartão sem CVV."""
        cartao_data = {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01"
        }

        response = client.post("/validaCartaoDeCredito", json=cartao_data)

        assert response.status_code == 422

    def test_valida_cartao_sem_nome(self, client):
        """Testa validação de cartão sem nome do titular."""
        cartao_data = {
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        response = client.post("/validaCartaoDeCredito", json=cartao_data)

        assert response.status_code == 422

    def test_valida_cartao_body_vazio(self, client):
        """Testa validação de cartão com body vazio."""
        response = client.post("/validaCartaoDeCredito", json={})

        assert response.status_code == 422

    def test_valida_cartao_sem_body(self, client):
        """Testa validação de cartão sem body."""
        response = client.post("/validaCartaoDeCredito")

        assert response.status_code == 422

