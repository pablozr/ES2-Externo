"""
Testes de integração para a API de cartão de crédito.
Testa o fluxo completo de validação de cartão através da API.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routes.cartao.router import router


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


class TestCartaoIntegration:
    """Testes de integração para validação de cartão."""

    def test_fluxo_completo_validacao_cartao_aprovado(self, client, sample_cartao):
        """
        Testa o fluxo completo de validação de cartão com aprovação.
        
        Cenário: Cliente envia dados de cartão válidos
        Resultado esperado: Cartão é validado com sucesso
        """
        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            # Simula resposta de sucesso do Mercado Pago
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": True,
                "mensagem": "Cartão válido"
            })

            response = client.post("/validaCartaoDeCredito", json=sample_cartao)

            # Verifica resposta
            assert response.status_code == 200
            assert response.json() == "Cartão válido"
            
            # Verifica que o serviço foi chamado corretamente
            mock_mp.valida_cartao.assert_called_once()
            call_args = mock_mp.valida_cartao.call_args[0][0]
            assert call_args["numero"] == sample_cartao["numero"]
            assert call_args["nomeTitular"] == sample_cartao["nomeTitular"]

    def test_fluxo_completo_validacao_cartao_rejeitado(self, client, sample_cartao):
        """
        Testa o fluxo completo de validação de cartão rejeitado.
        
        Cenário: Cliente envia dados de cartão que são rejeitados pelo gateway
        Resultado esperado: API retorna erro 400 com mensagem apropriada
        """
        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": False,
                "mensagem": "Cartão expirado"
            })

            response = client.post("/validaCartaoDeCredito", json=sample_cartao)

            assert response.status_code == 400
            assert response.json()["codigo"] == 400
            assert "Cartão expirado" in response.json()["mensagem"]

    def test_fluxo_validacao_com_diferentes_bandeiras(self, client):
        """
        Testa validação de cartões de diferentes bandeiras.
        
        Cenário: Validar cartões Visa, Mastercard e Amex
        """
        cartoes = [
            {
                "nomeTitular": "APRO",
                "numero": "4509953566233704",  # Visa
                "validade": "2030-12-01",
                "cvv": "123"
            },
            {
                "nomeTitular": "APRO",
                "numero": "5031433215406351",  # Mastercard
                "validade": "2030-12-01",
                "cvv": "123"
            },
            {
                "nomeTitular": "APRO",
                "numero": "371180303257522",  # Amex (15 dígitos)
                "validade": "2030-12-01",
                "cvv": "1234"
            }
        ]

        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": True,
                "mensagem": "Cartão válido"
            })

            for cartao in cartoes:
                response = client.post("/validaCartaoDeCredito", json=cartao)
                assert response.status_code == 200, f"Falhou para cartão: {cartao['numero'][:4]}..."

    def test_fluxo_validacao_com_erro_gateway(self, client, sample_cartao):
        """
        Testa comportamento quando o gateway de pagamento está indisponível.
        
        Cenário: Gateway retorna erro de timeout/conexão
        Resultado esperado: API retorna erro 500
        """
        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(
                side_effect=Exception("Connection timeout")
            )

            response = client.post("/validaCartaoDeCredito", json=sample_cartao)

            assert response.status_code == 500
            assert "mensagem" in response.json()

    def test_fluxo_validacao_dados_parciais(self, client):
        """
        Testa validação com dados parciais/incompletos.
        
        Cenário: Cliente envia requisição sem todos os campos obrigatórios
        Resultado esperado: API retorna erro 422 de validação
        """
        casos_invalidos = [
            {"numero": "4509953566233704", "validade": "2030-12-01", "cvv": "123"},  # Sem nomeTitular
            {"nomeTitular": "APRO", "validade": "2030-12-01", "cvv": "123"},  # Sem numero
            {"nomeTitular": "APRO", "numero": "4509953566233704", "cvv": "123"},  # Sem validade
            {"nomeTitular": "APRO", "numero": "4509953566233704", "validade": "2030-12-01"},  # Sem cvv
        ]

        for caso in casos_invalidos:
            response = client.post("/validaCartaoDeCredito", json=caso)
            assert response.status_code == 422, f"Deveria falhar para: {caso}"

    def test_fluxo_validacao_formato_validade_incorreto(self, client):
        """
        Testa validação com formato de validade incorreto.
        
        Cenário: Diferentes formatos inválidos de data de validade
        """
        formatos_invalidos = [
            "12/2030",      # MM/YYYY
            "12-2030",      # MM-YYYY
            "2030/12/01",   # YYYY/MM/DD
            "01-12-2030",   # DD-MM-YYYY
            "12/01/2030",   # MM/DD/YYYY
        ]

        for formato in formatos_invalidos:
            cartao = {
                "nomeTitular": "APRO",
                "numero": "4509953566233704",
                "validade": formato,
                "cvv": "123"
            }
            response = client.post("/validaCartaoDeCredito", json=cartao)
            assert response.status_code == 422, f"Deveria rejeitar formato: {formato}"

    def test_fluxo_multiplas_validacoes_sequenciais(self, client, sample_cartao):
        """
        Testa múltiplas validações sequenciais (simula alta carga).
        
        Cenário: Várias requisições de validação em sequência
        """
        with patch("routes.cartao.router.mercado_pago_instance") as mock_mp:
            mock_mp.valida_cartao = AsyncMock(return_value={
                "status": True,
                "mensagem": "Cartão válido"
            })

            resultados = []
            for _ in range(10):
                response = client.post("/validaCartaoDeCredito", json=sample_cartao)
                resultados.append(response.status_code)

            # Todas as requisições devem ter sucesso
            assert all(status == 200 for status in resultados)
            assert mock_mp.valida_cartao.call_count == 10

