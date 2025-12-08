import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from functions.email.email_manager import EmailManager


class TestEmailManager:
    """Testes para o EmailManager."""

    @pytest.fixture
    def email_data(self):
        """Dados de email para teste."""
        return {
            "email": "test@example.com",
            "assunto": "Teste de Email",
            "mensagem": "Esta é uma mensagem de teste"
        }

    @pytest.mark.asyncio
    async def test_send_email_sucesso(self, email_data):
        """Testa envio de email com sucesso."""
        with patch("functions.email.email_manager.FastMail") as mock_fastmail:
            mock_fm_instance = AsyncMock()
            mock_fm_instance.send_message = AsyncMock()
            mock_fastmail.return_value = mock_fm_instance

            email_manager = EmailManager()
            result = await email_manager.send_email(email_data)

            assert result["status"] is True
            assert result["data"]["email"] == email_data["email"]
            assert result["data"]["assunto"] == email_data["assunto"]
            assert result["data"]["mensagem"] == email_data["mensagem"]
            assert "id" in result["data"]

    @pytest.mark.asyncio
    async def test_send_email_erro(self, email_data):
        """Testa envio de email com erro."""
        with patch("functions.email.email_manager.FastMail") as mock_fastmail:
            mock_fm_instance = AsyncMock()
            mock_fm_instance.send_message.side_effect = Exception("SMTP Error")
            mock_fastmail.return_value = mock_fm_instance

            email_manager = EmailManager()
            result = await email_manager.send_email(email_data)

            assert result["codigo"] == 404
            assert "mensagem" in result

    @pytest.mark.asyncio
    async def test_send_email_retorna_id_aleatorio(self, email_data):
        """Testa que o ID retornado é um número aleatório."""
        with patch("functions.email.email_manager.FastMail") as mock_fastmail:
            mock_fm_instance = AsyncMock()
            mock_fm_instance.send_message = AsyncMock()
            mock_fastmail.return_value = mock_fm_instance

            email_manager = EmailManager()
            result = await email_manager.send_email(email_data)

            assert isinstance(result["data"]["id"], int)
            assert 1 <= result["data"]["id"] <= 1000

    @pytest.mark.asyncio
    async def test_send_email_conexao_timeout(self, email_data):
        """Testa envio de email com timeout de conexão."""
        with patch("functions.email.email_manager.FastMail") as mock_fastmail:
            mock_fm_instance = AsyncMock()
            mock_fm_instance.send_message.side_effect = Exception("Connection timeout")
            mock_fastmail.return_value = mock_fm_instance

            email_manager = EmailManager()
            result = await email_manager.send_email(email_data)

            assert result["codigo"] == 404

    @pytest.mark.asyncio
    async def test_send_email_com_html(self):
        """Testa envio de email com conteúdo HTML."""
        email_data = {
            "email": "test@example.com",
            "assunto": "Email HTML",
            "mensagem": "<h1>Título</h1><p>Parágrafo de teste</p>"
        }

        with patch("functions.email.email_manager.FastMail") as mock_fastmail:
            mock_fm_instance = AsyncMock()
            mock_fm_instance.send_message = AsyncMock()
            mock_fastmail.return_value = mock_fm_instance

            email_manager = EmailManager()
            result = await email_manager.send_email(email_data)

            assert result["status"] is True
            assert result["data"]["mensagem"] == email_data["mensagem"]

    @pytest.mark.asyncio
    async def test_send_email_assunto_longo(self):
        """Testa envio de email com assunto longo."""
        email_data = {
            "email": "test@example.com",
            "assunto": "A" * 500,
            "mensagem": "Mensagem normal"
        }

        with patch("functions.email.email_manager.FastMail") as mock_fastmail:
            mock_fm_instance = AsyncMock()
            mock_fm_instance.send_message = AsyncMock()
            mock_fastmail.return_value = mock_fm_instance

            email_manager = EmailManager()
            result = await email_manager.send_email(email_data)

            assert result["status"] is True
            assert len(result["data"]["assunto"]) == 500

    @pytest.mark.asyncio
    async def test_send_email_mensagem_longa(self):
        """Testa envio de email com mensagem longa."""
        email_data = {
            "email": "test@example.com",
            "assunto": "Assunto normal",
            "mensagem": "B" * 10000
        }

        with patch("functions.email.email_manager.FastMail") as mock_fastmail:
            mock_fm_instance = AsyncMock()
            mock_fm_instance.send_message = AsyncMock()
            mock_fastmail.return_value = mock_fm_instance

            email_manager = EmailManager()
            result = await email_manager.send_email(email_data)

            assert result["status"] is True
            assert len(result["data"]["mensagem"]) == 10000

