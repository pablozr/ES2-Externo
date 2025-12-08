import pytest
from unittest.mock import patch, MagicMock

from functions.mercado_pago.mercado_pago_manager import MercadoPagoManager


class TestMercadoPagoManager:
    """Testes para o MercadoPagoManager."""

    @pytest.fixture
    def mercado_pago_manager(self):
        """Instância do MercadoPagoManager para testes."""
        return MercadoPagoManager()

    @pytest.fixture
    def cartao_valido(self):
        """Dados de cartão válido."""
        return {
            "nomeTitular": "APRO",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

    @pytest.mark.asyncio
    async def test_valida_cartao_sucesso(self, mercado_pago_manager, cartao_valido):
        """Testa validação de cartão com sucesso."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 201,
                "response": {"id": "test_token"}
            }

            result = await mercado_pago_manager.valida_cartao(cartao_valido)

            assert result["status"] is True
            assert result["mensagem"] == "Cartão válido"

    @pytest.mark.asyncio
    async def test_valida_cartao_dados_invalidos(self, mercado_pago_manager, cartao_valido):
        """Testa validação de cartão com dados inválidos."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 400,
                "response": {"message": "Invalid card data"}
            }

            result = await mercado_pago_manager.valida_cartao(cartao_valido)

            assert result["codigo"] == 422
            assert result["mensagem"] == "Dados Inválidos"

    @pytest.mark.asyncio
    async def test_valida_cartao_excecao(self, mercado_pago_manager, cartao_valido):
        """Testa validação de cartão quando ocorre exceção."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.side_effect = Exception("API Error")

            result = await mercado_pago_manager.valida_cartao(cartao_valido)

            assert result["status"] is False
            assert "Erro ao validar" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_valida_cartao_com_espacos_no_numero(self, mercado_pago_manager):
        """Testa validação de cartão com espaços no número."""
        cartao = {
            "nomeTitular": "APRO",
            "numero": "4509 9535 6623 3704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 201,
                "response": {"id": "test_token"}
            }

            result = await mercado_pago_manager.valida_cartao(cartao)

            assert result["status"] is True

    @pytest.mark.asyncio
    async def test_realiza_pagamento_sucesso(self, mercado_pago_manager, cartao_valido):
        """Testa realização de pagamento com sucesso."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 201,
                "response": {"id": "test_token_id"}
            }
            mock_sdk.payment.return_value.create.return_value = {
                "response": {"status": "approved"}
            }

            result = await mercado_pago_manager.realiza_pagamento(cartao_valido, 100.00)

            assert result["status"] is True

    @pytest.mark.asyncio
    async def test_realiza_pagamento_token_invalido(self, mercado_pago_manager, cartao_valido):
        """Testa pagamento quando token é inválido."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 400,
                "response": {"message": "Invalid"}
            }

            result = await mercado_pago_manager.realiza_pagamento(cartao_valido, 100.00)

            assert result["status"] is False
            assert result["mensagem"] == "Dados invalidos"

    @pytest.mark.asyncio
    async def test_realiza_pagamento_rejeitado(self, mercado_pago_manager, cartao_valido):
        """Testa quando pagamento é rejeitado."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 201,
                "response": {"id": "test_token_id"}
            }
            mock_sdk.payment.return_value.create.return_value = {
                "response": {
                    "status": "rejected",
                    "status_detail": "cc_rejected_insufficient_amount"
                }
            }

            result = await mercado_pago_manager.realiza_pagamento(cartao_valido, 100.00)

            assert result["status"] is False
            assert "mensagem" in result

    @pytest.mark.asyncio
    async def test_realiza_pagamento_pendente(self, mercado_pago_manager, cartao_valido):
        """Testa quando pagamento fica pendente."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 201,
                "response": {"id": "test_token_id"}
            }
            mock_sdk.payment.return_value.create.return_value = {
                "response": {"status": "pending"}
            }

            result = await mercado_pago_manager.realiza_pagamento(cartao_valido, 100.00)

            assert result["status"] is False

    @pytest.mark.asyncio
    async def test_realiza_pagamento_excecao(self, mercado_pago_manager, cartao_valido):
        """Testa quando ocorre exceção durante pagamento."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.side_effect = Exception("API Error")

            result = await mercado_pago_manager.realiza_pagamento(cartao_valido, 100.00)

            assert result["status"] is False
            assert result["mensagem"] == "Erro interno"

    @pytest.mark.asyncio
    async def test_realiza_pagamento_valor_decimal(self, mercado_pago_manager, cartao_valido):
        """Testa pagamento com valor decimal."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 201,
                "response": {"id": "test_token_id"}
            }
            mock_sdk.payment.return_value.create.return_value = {
                "response": {"status": "approved"}
            }

            result = await mercado_pago_manager.realiza_pagamento(cartao_valido, 99.99)

            assert result["status"] is True

    @pytest.mark.asyncio
    async def test_realiza_pagamento_valor_grande(self, mercado_pago_manager, cartao_valido):
        """Testa pagamento com valor grande."""
        with patch("functions.mercado_pago.mercado_pago_manager.sdk") as mock_sdk:
            mock_sdk.card_token.return_value.create.return_value = {
                "status": 201,
                "response": {"id": "test_token_id"}
            }
            mock_sdk.payment.return_value.create.return_value = {
                "response": {"status": "approved"}
            }

            result = await mercado_pago_manager.realiza_pagamento(cartao_valido, 10000.00)

            assert result["status"] is True

