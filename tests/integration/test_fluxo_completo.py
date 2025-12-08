"""
Testes de integração de fluxo completo (End-to-End).
Testa cenários completos que envolvem múltiplos componentes do sistema.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.cartao.router import router as cartao_router
from routes.cobranca.router import router as cobranca_router
from routes.email.router import router as email_router


class MockAsyncContextManager:
    """Helper para simular async context manager."""
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


@pytest.fixture
def app_completa():
    """Cria aplicação FastAPI com todas as rotas."""
    app = FastAPI()
    app.include_router(cartao_router)
    app.include_router(cobranca_router)
    app.include_router(email_router)
    return app


@pytest.fixture
def client(app_completa):
    """Cliente de teste."""
    return TestClient(app_completa)


class TestFluxoAluguelBicicleta:
    """
    Testes de integração para o fluxo completo de aluguel de bicicleta.
    
    Cenário típico:
    1. Ciclista tem cartão validado no cadastro
    2. Ciclista aluga bicicleta
    3. Sistema realiza cobrança
    4. Sistema envia email de confirmação
    """

    def test_fluxo_aluguel_completo_sucesso(self, client):
        """
        Testa o fluxo completo de aluguel com sucesso.
        
        Passos:
        1. Validar cartão do ciclista
        2. Realizar cobrança do aluguel
        3. Enviar email de confirmação
        """
        # Dados do ciclista
        cartao = {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }
        cobranca = {"valor": 15.00, "ciclista": 1}
        email = {
            "email": "ciclista@example.com",
            "assunto": "Confirmação de Aluguel",
            "mensagem": "<h1>Aluguel confirmado!</h1><p>Valor: R$ 15,00</p>"
        }

        # Passo 1: Validar cartão
        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": True,
                "mensagem": "Cartão válido"
            })

            response_cartao = client.post("/validaCartaoDeCredito", json=cartao)
            assert response_cartao.status_code == 200

        # Passo 2: Realizar cobrança
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            mock_db.realizar_cobranca = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "FINALIZADA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": "2024-01-01T10:00:05",
                    "valor": 15.00,
                    "ciclista": 1
                }
            })

            response_cobranca = client.post("/cobranca", json=cobranca)
            assert response_cobranca.status_code == 200
            assert response_cobranca.json()["status"] == "FINALIZADA"

        # Passo 3: Enviar email de confirmação
        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 123,
                    "email": email["email"],
                    "assunto": email["assunto"],
                    "mensagem": email["mensagem"]
                }
            })

            response_email = client.post("/enviarEmail", json=email)
            assert response_email.status_code == 200

    def test_fluxo_aluguel_cartao_invalido(self, client):
        """
        Testa fluxo quando cartão é inválido.
        
        Resultado esperado: Fluxo interrompido na validação
        """
        cartao = {
            "nomeTitular": "OTHE",  # Nome que indica rejeição no sandbox
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": False,
                "mensagem": "Cartão rejeitado"
            })

            response = client.post("/validaCartaoDeCredito", json=cartao)
            
            # Fluxo deve parar aqui - cartão inválido
            assert response.status_code == 400

    def test_fluxo_aluguel_cobranca_falha(self, client):
        """
        Testa fluxo quando cobrança falha após validação.
        
        Cenário: Cartão válido mas sem saldo
        """
        cartao = {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }
        cobranca = {"valor": 15.00, "ciclista": 1}

        # Cartão válido
        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": True,
                "mensagem": "Cartão válido"
            })
            response_cartao = client.post("/validaCartaoDeCredito", json=cartao)
            assert response_cartao.status_code == 200

        # Cobrança falha
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            mock_db.realizar_cobranca = AsyncMock(return_value={
                "status": False,
                "mensagem": "Saldo insuficiente"
            })

            response_cobranca = client.post("/cobranca", json=cobranca)
            assert response_cobranca.status_code == 400


class TestFluxoFilaCobrancas:
    """
    Testes de integração para o fluxo de fila de cobranças.
    
    Cenário: Sistema processa cobranças em lote durante horário de baixa demanda.
    """

    def test_fluxo_adicionar_e_processar_fila(self, client):
        """
        Testa adicionar múltiplas cobranças à fila e processar.
        """
        cobrancas = [
            {"valor": 10.00, "ciclista": 1},
            {"valor": 20.00, "ciclista": 2},
            {"valor": 15.00, "ciclista": 3}
        ]

        # Adicionar cobranças à fila
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            for i, cobranca in enumerate(cobrancas):
                mock_db.colocar_cobranca_na_fila = AsyncMock(return_value={
                    "status": True,
                    "data": {
                        "id": i + 1,
                        "status": "EM_FILA",
                        "hora_solicitacao": "2024-01-01T10:00:00",
                        "hora_finalizacao": None,
                        "valor": cobranca["valor"],
                        "ciclista": cobranca["ciclista"]
                    }
                })

                response = client.post("/filaCobranca", json=cobranca)
                assert response.status_code == 200
                assert response.json()["status"] == "EM_FILA"

        # Processar fila
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            mock_db.processar_fila_cobrancas = AsyncMock(return_value={
                "status": True,
                "data": [
                    {
                        "id": i + 1,
                        "status": "FINALIZADA",
                        "hora_solicitacao": "2024-01-01T10:00:00",
                        "hora_finalizacao": "2024-01-01T10:05:00",
                        "valor": c["valor"],
                        "ciclista": c["ciclista"]
                    }
                    for i, c in enumerate(cobrancas)
                ]
            })

            response = client.post("/processaCobrancasEmFila")
            assert response.status_code == 200
            assert len(response.json()) == 3
            assert all(c["status"] == "FINALIZADA" for c in response.json())


class TestFluxoNotificacoes:
    """
    Testes de integração para o fluxo de notificações por email.
    """

    def test_fluxo_notificacao_cobranca_realizada(self, client):
        """
        Testa envio de notificação após cobrança realizada.
        """
        # Realizar cobrança
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            mock_db.realizar_cobranca = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 1,
                    "status": "FINALIZADA",
                    "hora_solicitacao": "2024-01-01T10:00:00",
                    "hora_finalizacao": "2024-01-01T10:00:05",
                    "valor": 25.50,
                    "ciclista": 1
                }
            })

            response_cobranca = client.post(
                "/cobranca", 
                json={"valor": 25.50, "ciclista": 1}
            )
            assert response_cobranca.status_code == 200
            cobranca_data = response_cobranca.json()

        # Enviar notificação
        email_notificacao = {
            "email": "ciclista@example.com",
            "assunto": f"Cobrança #{cobranca_data['id']} realizada",
            "mensagem": f"""
                <h2>Cobrança Realizada</h2>
                <p>ID: {cobranca_data['id']}</p>
                <p>Valor: R$ {cobranca_data['valor']:.2f}</p>
                <p>Status: {cobranca_data['status']}</p>
            """
        }

        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(return_value={
                "status": True,
                "data": {
                    "id": 100,
                    "email": email_notificacao["email"],
                    "assunto": email_notificacao["assunto"],
                    "mensagem": email_notificacao["mensagem"]
                }
            })

            response_email = client.post("/enviarEmail", json=email_notificacao)
            assert response_email.status_code == 200


class TestFluxoConsultas:
    """
    Testes de integração para consultas de cobranças.
    """

    def test_fluxo_criar_e_consultar_cobranca(self, client):
        """
        Testa criar uma cobrança e depois consultá-la.
        """
        cobranca_criada = {
            "id": 42,
            "status": "FINALIZADA",
            "hora_solicitacao": "2024-01-01T10:00:00",
            "hora_finalizacao": "2024-01-01T10:00:05",
            "valor": 100.00,
            "ciclista": 1
        }

        # Criar cobrança
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            mock_db.realizar_cobranca = AsyncMock(return_value={
                "status": True,
                "data": cobranca_criada
            })

            response_criar = client.post(
                "/cobranca",
                json={"valor": 100.00, "ciclista": 1}
            )
            assert response_criar.status_code == 200
            id_cobranca = response_criar.json()["id"]

        # Consultar cobrança
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            mock_db.get_cobranca_by_id = AsyncMock(return_value={
                "status": True,
                "data": cobranca_criada
            })

            response_consultar = client.get(f"/cobranca/{id_cobranca}")
            assert response_consultar.status_code == 200
            assert response_consultar.json()["id"] == id_cobranca
            assert response_consultar.json()["valor"] == 100.00


class TestFluxoErros:
    """
    Testes de integração para cenários de erro.
    """

    def test_fluxo_servicos_indisponiveis(self, client):
        """
        Testa comportamento quando serviços externos estão indisponíveis.
        """
        # Gateway de pagamento indisponível
        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(
                side_effect=Exception("Service unavailable")
            )

            response = client.post("/validaCartaoDeCredito", json={
                "nomeTitular": "APRO",
                "numero": "4509953566233704",
                "validade": "2030-12-01",
                "cvv": "123"
            })
            assert response.status_code == 500

        # Banco de dados indisponível
        with patch("routes.cobranca.router.asyncpg_manager") as mock_db:
            mock_db.realizar_cobranca = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            response = client.post("/cobranca", json={
                "valor": 100.00,
                "ciclista": 1
            })
            assert response.status_code == 500

        # Servidor de email indisponível
        with patch("routes.email.router.email_instance") as mock_email:
            mock_email.send_email = AsyncMock(
                side_effect=Exception("SMTP server unavailable")
            )

            response = client.post("/enviarEmail", json={
                "email": "test@example.com",
                "assunto": "Teste",
                "mensagem": "Mensagem"
            })
            assert response.status_code == 500

    def test_fluxo_dados_invalidos_em_todas_rotas(self, client):
        """
        Testa validação de dados inválidos em todas as rotas.
        """
        # Cartão inválido
        response = client.post("/validaCartaoDeCredito", json={})
        assert response.status_code == 422

        # Cobrança inválida
        response = client.post("/cobranca", json={})
        assert response.status_code == 422

        # Email inválido
        response = client.post("/enviarEmail", json={})
        assert response.status_code == 422

        # ID inválido
        response = client.get("/cobranca/abc")
        assert response.status_code == 422

