import pytest
from pydantic import ValidationError

from entities.cobranca.cobranca import CobrancaRequest


class TestCobrancaRequest:
    """Testes para a entidade CobrancaRequest."""

    def test_cobranca_valida(self):
        """Testa criação de cobrança com dados válidos."""
        cobranca = CobrancaRequest(valor=100.50, ciclista=1)
        assert cobranca.valor == 100.50
        assert cobranca.ciclista == 1

    def test_cobranca_valor_inteiro(self):
        """Testa cobrança com valor inteiro convertido para float."""
        cobranca = CobrancaRequest(valor=100, ciclista=1)
        assert cobranca.valor == 100.0
        assert isinstance(cobranca.valor, float)

    def test_cobranca_valor_zero(self):
        """Testa cobrança com valor zero."""
        cobranca = CobrancaRequest(valor=0.0, ciclista=1)
        assert cobranca.valor == 0.0

    def test_cobranca_valor_negativo(self):
        """Testa cobrança com valor negativo (aceito pelo modelo base)."""
        cobranca = CobrancaRequest(valor=-50.0, ciclista=1)
        assert cobranca.valor == -50.0

    def test_cobranca_ciclista_zero(self):
        """Testa cobrança com ciclista ID zero."""
        cobranca = CobrancaRequest(valor=100.0, ciclista=0)
        assert cobranca.ciclista == 0

    def test_cobranca_sem_valor(self):
        """Testa que cobrança sem valor falha."""
        with pytest.raises(ValidationError):
            CobrancaRequest(ciclista=1)

    def test_cobranca_sem_ciclista(self):
        """Testa que cobrança sem ciclista falha."""
        with pytest.raises(ValidationError):
            CobrancaRequest(valor=100.0)

    def test_cobranca_valor_string_invalida(self):
        """Testa que cobrança com valor string inválida falha."""
        with pytest.raises(ValidationError):
            CobrancaRequest(valor="cem", ciclista=1)

    def test_cobranca_ciclista_string_invalida(self):
        """Testa que cobrança com ciclista string inválida falha."""
        with pytest.raises(ValidationError):
            CobrancaRequest(valor=100.0, ciclista="um")

    def test_cobranca_model_dump(self):
        """Testa que model_dump retorna dicionário correto."""
        cobranca = CobrancaRequest(valor=150.75, ciclista=5)
        data = cobranca.model_dump()
        assert data == {"valor": 150.75, "ciclista": 5}

    def test_cobranca_valor_grande(self):
        """Testa cobrança com valor grande."""
        cobranca = CobrancaRequest(valor=999999.99, ciclista=1)
        assert cobranca.valor == 999999.99

    def test_cobranca_valor_pequeno(self):
        """Testa cobrança com valor pequeno."""
        cobranca = CobrancaRequest(valor=0.01, ciclista=1)
        assert cobranca.valor == 0.01

