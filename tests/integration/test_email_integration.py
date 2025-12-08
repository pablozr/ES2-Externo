"""
Testes de integração para a API de email.
Testa o fluxo completo de envio de emails através da API.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.email.router import router


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


class TestEmailIntegration:
    """Testes de integração para envio de emails."""

    def test_fluxo_completo_envio_email_sucesso(self, client, sample_email):
        """
        Testa o fluxo completo de envio de email com sucesso.
        
        Cenário: Sistema envia email de notificação ao ciclista
        Resultado esperado: Email enviado e registro criado
        """
        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 123,
                    "email": sample_email["email"],
                    "assunto": sample_email["assunto"],
                    "mensagem": sample_email["mensagem"]
                }
            })

            response = client.post("/enviarEmail", json=sample_email)

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == sample_email["email"]
            assert data["assunto"] == sample_email["assunto"]
            assert "id" in data

    def test_fluxo_envio_email_falha_smtp(self, client, sample_email):
        """
        Testa comportamento quando servidor SMTP está indisponível.
        
        Cenário: Servidor de email não responde
        """
        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": False,
                "message": "SMTP connection failed"
            })

            response = client.post("/enviarEmail", json=sample_email)

            assert response.status_code == 404

    def test_fluxo_envio_email_erro_interno(self, client, sample_email):
        """
        Testa comportamento quando ocorre erro interno.
        """
        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(
                side_effect=Exception("Internal error")
            )

            response = client.post("/enviarEmail", json=sample_email)

            assert response.status_code == 500

    def test_fluxo_envio_email_notificacao_cobranca(self, client):
        """
        Testa envio de email de notificação de cobrança.
        
        Cenário: Sistema notifica ciclista sobre cobrança realizada
        """
        email_cobranca = {
            "email": "ciclista@example.com",
            "assunto": "Cobrança realizada - Aluguel de Bicicleta",
            "mensagem": """
                <h1>Cobrança Realizada</h1>
                <p>Prezado(a) Cliente,</p>
                <p>Informamos que foi realizada uma cobrança no valor de R$ 15,00 
                referente ao aluguel de bicicleta.</p>
                <p>Detalhes:</p>
                <ul>
                    <li>Data: 01/01/2024</li>
                    <li>Valor: R$ 15,00</li>
                    <li>Duração: 30 minutos</li>
                </ul>
                <p>Obrigado por usar nosso serviço!</p>
            """
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 456,
                    "email": email_cobranca["email"],
                    "assunto": email_cobranca["assunto"],
                    "mensagem": email_cobranca["mensagem"]
                }
            })

            response = client.post("/enviarEmail", json=email_cobranca)

            assert response.status_code == 200
            assert "Cobrança" in response.json()["assunto"]

    def test_fluxo_envio_email_boas_vindas(self, client):
        """
        Testa envio de email de boas-vindas para novo ciclista.
        """
        email_boas_vindas = {
            "email": "novo.ciclista@example.com",
            "assunto": "Bem-vindo ao Sistema de Aluguel de Bicicletas!",
            "mensagem": """
                <h1>Bem-vindo!</h1>
                <p>Seu cadastro foi realizado com sucesso.</p>
                <p>Agora você pode alugar bicicletas em qualquer estação.</p>
            """
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 789,
                    "email": email_boas_vindas["email"],
                    "assunto": email_boas_vindas["assunto"],
                    "mensagem": email_boas_vindas["mensagem"]
                }
            })

            response = client.post("/enviarEmail", json=email_boas_vindas)

            assert response.status_code == 200

    def test_fluxo_envio_emails_diferentes_dominios(self, client):
        """
        Testa envio de emails para diferentes domínios.
        
        Cenário: Emails para Gmail, Hotmail, domínios corporativos
        """
        emails = [
            "usuario@gmail.com",
            "usuario@hotmail.com",
            "usuario@outlook.com",
            "usuario@empresa.com.br",
            "usuario@universidade.edu.br"
        ]

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "email": "",
                    "assunto": "Teste",
                    "mensagem": "Teste"
                }
            })

            for email_addr in emails:
                email_data = {
                    "email": email_addr,
                    "assunto": "Teste de Domínio",
                    "mensagem": "Mensagem de teste"
                }
                mock_email.send_email.return_value["data"]["email"] = email_addr
                
                response = client.post("/enviarEmail", json=email_data)
                assert response.status_code == 200, f"Falhou para: {email_addr}"

    def test_fluxo_envio_email_com_caracteres_especiais(self, client):
        """
        Testa envio de email com caracteres especiais no conteúdo.
        """
        email_especial = {
            "email": "teste@example.com",
            "assunto": "Notificação: Ação necessária! ⚠️",
            "mensagem": """
                <p>Olá João,</p>
                <p>Caracteres especiais: ã é í ó ú ç</p>
                <p>Símbolos: € $ £ ¥</p>
                <p>Emojis: 🚲 ✅ ❌</p>
            """
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 100,
                    "email": email_especial["email"],
                    "assunto": email_especial["assunto"],
                    "mensagem": email_especial["mensagem"]
                }
            })

            response = client.post("/enviarEmail", json=email_especial)

            assert response.status_code == 200

    def test_fluxo_envio_multiplos_emails_sequenciais(self, client, sample_email):
        """
        Testa envio de múltiplos emails em sequência.
        """
        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "email": sample_email["email"],
                    "assunto": sample_email["assunto"],
                    "mensagem": sample_email["mensagem"]
                }
            })

            resultados = []
            for i in range(10):
                response = client.post("/enviarEmail", json=sample_email)
                resultados.append(response.status_code)

            assert all(status == 200 for status in resultados)
            assert mock_email.send_email.call_count == 10

    def test_fluxo_validacao_email_invalido(self, client):
        """
        Testa rejeição de emails com formato inválido.
        """
        emails_invalidos = [
            {"email": "invalido", "assunto": "Teste", "mensagem": "Msg"},
            {"email": "invalido@", "assunto": "Teste", "mensagem": "Msg"},
            {"email": "@dominio.com", "assunto": "Teste", "mensagem": "Msg"},
            {"email": "user@.com", "assunto": "Teste", "mensagem": "Msg"},
        ]

        for email_data in emails_invalidos:
            response = client.post("/enviarEmail", json=email_data)
            assert response.status_code == 422, f"Deveria rejeitar: {email_data['email']}"

    def test_fluxo_email_campos_vazios(self, client):
        """
        Testa rejeição de emails com campos obrigatórios faltando.
        """
        # Apenas campos faltando são rejeitados com 422
        casos_faltando = [
            {"assunto": "Teste", "mensagem": "Msg"},  # Sem email
            {"email": "test@example.com", "mensagem": "Msg"},  # Sem assunto
            {"email": "test@example.com", "assunto": "Teste"},  # Sem mensagem
        ]

        for caso in casos_faltando:
            response = client.post("/enviarEmail", json=caso)
            assert response.status_code == 422, f"Deveria retornar 422 para: {caso}"

