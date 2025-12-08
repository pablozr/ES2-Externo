"""
Configurações e fixtures para testes de integração.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Configurar variáveis de ambiente antes de importar a aplicação
os.environ["DB_URL"] = "postgresql://test:test@localhost:5432/test"
os.environ["CICLISTA_SERVICE_URL"] = "http://localhost:8080/ciclistas/"
os.environ["MP_ACCESS_TOKEN"] = "TEST_TOKEN"
os.environ["MAIL_USERNAME"] = "test@test.com"
os.environ["MAIL_PASSWORD"] = "test_password"
os.environ["MAIL_FROM"] = "test@test.com"
os.environ["MAIL_PORT"] = "587"
os.environ["MAIL_SERVER"] = "smtp.test.com"


class MockAsyncContextManager:
    """Helper class para simular async context manager do pool."""
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def mock_db_pool():
    """Mock para o pool de conexões do banco de dados."""
    pool = MagicMock()
    connection = AsyncMock()
    
    pool.acquire.return_value = MockAsyncContextManager(connection)
    pool.close = AsyncMock()
    
    return pool, connection


@pytest.fixture
def mock_all_external_services(mock_db_pool):
    """
    Mock de todos os serviços externos para testes de integração.
    Isso permite testar a integração entre componentes internos
    sem depender de serviços externos reais.
    """
    pool, connection = mock_db_pool
    
    with patch("functions.database.asyncpg_manager.asyncpg_manager") as mock_asyncpg:
        mock_asyncpg.pool = pool
        mock_asyncpg.connect = AsyncMock()
        mock_asyncpg.disconnect = AsyncMock()
        
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            with patch("functions.email.email_manager.FastMail") as mock_fastmail:
                with patch("httpx.AsyncClient") as mock_httpx:
                    yield {
                        "asyncpg": mock_asyncpg,
                        "pool": pool,
                        "connection": connection,
                        "sdk": mock_sdk,
                        "fastmail": mock_fastmail,
                        "httpx": mock_httpx
                    }


@pytest.fixture
def app_client(mock_all_external_services):
    """
    Cliente de teste com todos os serviços externos mockados.
    """
    from main import app
    
    with TestClient(app) as client:
        yield client, mock_all_external_services


@pytest.fixture
def sample_cartao():
    """Dados de cartão válido para testes."""
    return {
        "nomeTitular": "APRO",
        "numero": "4509953566233704",
        "validade": "2030-12-01",
        "cvv": "123"
    }


@pytest.fixture
def sample_cobranca():
    """Dados de cobrança válida para testes."""
    return {
        "valor": 100.00,
        "ciclista": 1
    }


@pytest.fixture
def sample_email():
    """Dados de email válido para testes."""
    return {
        "email": "test@example.com",
        "assunto": "Teste de Integração",
        "mensagem": "Esta é uma mensagem de teste de integração"
    }

