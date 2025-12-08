import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Configurar variáveis de ambiente antes de importar qualquer módulo
os.environ["DB_URL"] = "postgresql://test:test@localhost:5432/test"
os.environ["CICLISTA_SERVICE_URL"] = "http://localhost:8080/ciclistas/"
os.environ["MP_ACCESS_TOKEN"] = "TEST_TOKEN"
os.environ["MAIL_USERNAME"] = "test@test.com"
os.environ["MAIL_PASSWORD"] = "test_password"
os.environ["MAIL_FROM"] = "test@test.com"
os.environ["MAIL_PORT"] = "587"
os.environ["MAIL_SERVER"] = "smtp.test.com"


@pytest.fixture
def mock_asyncpg_pool():
    """Mock para o pool de conexões do asyncpg."""
    pool = AsyncMock()
    connection = AsyncMock()
    
    pool.acquire.return_value.__aenter__.return_value = connection
    pool.acquire.return_value.__aexit__.return_value = None
    
    return pool, connection


@pytest.fixture
def mock_ciclista_manager():
    """Mock para o CiclistaManager."""
    with patch("functions.integration.ciclista_manager.ciclista_instance") as mock:
        mock.obter_cartao = AsyncMock()
        yield mock


@pytest.fixture
def mock_mercado_pago():
    """Mock para o MercadoPagoManager."""
    with patch("functions.mercado_pago.mercado_pago_manager.mercado_pago_instance") as mock:
        mock.valida_cartao = AsyncMock()
        mock.realiza_pagamento = AsyncMock()
        yield mock


@pytest.fixture
def mock_email_manager():
    """Mock para o EmailManager."""
    with patch("functions.email.email_manager.email_instance") as mock:
        mock.send_email = AsyncMock()
        yield mock


@pytest.fixture
def sample_cartao_data():
    """Dados de exemplo para um cartão válido."""
    return {
        "nomeTitular": "APRO",
        "numero": "4509953566233704",
        "validade": "2030-12-01",
        "cvv": "123"
    }


@pytest.fixture
def sample_cobranca_data():
    """Dados de exemplo para uma cobrança."""
    return {
        "valor": 100.00,
        "ciclista": 1
    }


@pytest.fixture
def sample_email_data():
    """Dados de exemplo para um email."""
    return {
        "email": "test@example.com",
        "assunto": "Teste",
        "mensagem": "Mensagem de teste"
    }


@pytest.fixture
def mock_sdk():
    """Mock para o SDK do Mercado Pago."""
    with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock:
        mock.card_token.return_value.create.return_value = {
            "status": 201,
            "response": {"id": "test_token_id"}
        }
        mock.payment.return_value.create.return_value = {
            "response": {"status": "approved"}
        }
        yield mock


@pytest.fixture
def mock_httpx_client():
    """Mock para o cliente HTTP."""
    with patch("httpx.AsyncClient") as mock:
        yield mock


@pytest.fixture
def mock_fastmail():
    """Mock para o FastMail."""
    with patch("functions.email.email_manager.FastMail") as mock:
        instance = AsyncMock()
        instance.send_message = AsyncMock()
        mock.return_value = instance
        yield mock

