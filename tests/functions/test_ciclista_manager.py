import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from functions.integration.ciclista_manager import CiclistaManager


class TestCiclistaManager:
    """Testes para o CiclistaManager."""

    @pytest.fixture
    def ciclista_manager(self):
        """Instância do CiclistaManager para testes."""
        return CiclistaManager()

    @pytest.mark.asyncio
    async def test_obter_cartao_sucesso(self, ciclista_manager):
        """Testa obtenção de cartão com sucesso."""
        cartao_data = {
            "nomeTitular": "João Silva",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = cartao_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client.return_value.__aexit__.return_value = None

            result = await ciclista_manager.obter_cartao(1)

            assert result["status"] is True
            assert result["data"] == cartao_data

    @pytest.mark.asyncio
    async def test_obter_cartao_ciclista_nao_encontrado(self, ciclista_manager):
        """Testa quando ciclista não é encontrado."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client.return_value.__aexit__.return_value = None

            result = await ciclista_manager.obter_cartao(999)

            assert result["status"] is False
            assert result["mensagem"] == "Ciclista não encontrado"

    @pytest.mark.asyncio
    async def test_obter_cartao_erro_servidor(self, ciclista_manager):
        """Testa quando o servidor retorna erro 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client.return_value.__aexit__.return_value = None

            result = await ciclista_manager.obter_cartao(1)

            assert result["status"] is False
            assert result["mensagem"] == "Ciclista não encontrado"

    @pytest.mark.asyncio
    async def test_obter_cartao_erro_conexao(self, ciclista_manager):
        """Testa quando há erro de conexão."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.RequestError("Connection error")
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client.return_value.__aexit__.return_value = None

            result = await ciclista_manager.obter_cartao(1)

            assert result["status"] is False
            assert result["mensagem"] == "Erro ao conectar ao serviço de ciclistas"

    @pytest.mark.asyncio
    async def test_obter_cartao_timeout(self, ciclista_manager):
        """Testa quando há timeout na requisição."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.RequestError("Timeout")
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client.return_value.__aexit__.return_value = None

            result = await ciclista_manager.obter_cartao(1)

            assert result["status"] is False
            assert "Erro ao conectar" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_obter_cartao_resposta_vazia(self, ciclista_manager):
        """Testa quando a resposta retorna dados vazios."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client.return_value.__aexit__.return_value = None

            result = await ciclista_manager.obter_cartao(1)

            assert result["status"] is True
            assert result["data"] == {}

    @pytest.mark.asyncio
    async def test_obter_cartao_status_401(self, ciclista_manager):
        """Testa quando retorna 401 Unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client.return_value.__aexit__.return_value = None

            result = await ciclista_manager.obter_cartao(1)

            assert result["status"] is False

