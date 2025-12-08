import pytest
from pydantic import ValidationError

from entities.cartao.cartao import Cartao


class TestCartao:
    """Testes para a entidade Cartao."""

    def test_cartao_valido(self):
        """Testa criação de cartão com dados válidos."""
        cartao = Cartao(
            nomeTitular="João Silva",
            numero="4509953566233704",
            validade="2030-12-01",
            cvv="123"
        )
        assert cartao.nomeTitular == "João Silva"
        assert cartao.numero == "4509953566233704"
        assert cartao.validade == "2030-12-01"
        assert cartao.cvv == "123"

    def test_cartao_numero_minimo(self):
        """Testa cartão com número mínimo de 13 dígitos."""
        cartao = Cartao(
            nomeTitular="João Silva",
            numero="4509953566233",  # 13 dígitos
            validade="2030-12-01",
            cvv="123"
        )
        assert len(cartao.numero) == 13

    def test_cartao_numero_maximo(self):
        """Testa cartão com número máximo de 19 dígitos."""
        cartao = Cartao(
            nomeTitular="João Silva",
            numero="4509953566233704123",  # 19 dígitos
            validade="2030-12-01",
            cvv="123"
        )
        assert len(cartao.numero) == 19

    def test_cartao_numero_muito_curto(self):
        """Testa que cartão com número muito curto falha validação."""
        with pytest.raises(ValidationError) as exc_info:
            Cartao(
                nomeTitular="João Silva",
                numero="123456789012",  # 12 dígitos (menos que 13)
                validade="2030-12-01",
                cvv="123"
            )
        assert "string_too_short" in str(exc_info.value)

    def test_cartao_numero_muito_longo(self):
        """Testa que cartão com número muito longo falha validação."""
        with pytest.raises(ValidationError) as exc_info:
            Cartao(
                nomeTitular="João Silva",
                numero="45099535662337041234",  # 20 dígitos (mais que 19)
                validade="2030-12-01",
                cvv="123"
            )
        assert "string_too_long" in str(exc_info.value)

    def test_cartao_validade_formato_invalido(self):
        """Testa que validade com formato inválido falha."""
        with pytest.raises(ValidationError) as exc_info:
            Cartao(
                nomeTitular="João Silva",
                numero="4509953566233704",
                validade="12/2030",  # formato inválido
                cvv="123"
            )
        assert "pattern" in str(exc_info.value).lower() or "string_pattern_mismatch" in str(exc_info.value)

    def test_cartao_validade_formato_dia_mes_ano(self):
        """Testa que validade no formato DD-MM-YYYY falha."""
        with pytest.raises(ValidationError):
            Cartao(
                nomeTitular="João Silva",
                numero="4509953566233704",
                validade="01-12-2030",  # formato inválido
                cvv="123"
            )

    def test_cartao_sem_nome_titular(self):
        """Testa que cartão sem nome do titular falha."""
        with pytest.raises(ValidationError):
            Cartao(
                numero="4509953566233704",
                validade="2030-12-01",
                cvv="123"
            )

    def test_cartao_sem_cvv(self):
        """Testa que cartão sem CVV falha."""
        with pytest.raises(ValidationError):
            Cartao(
                nomeTitular="João Silva",
                numero="4509953566233704",
                validade="2030-12-01"
            )

    def test_cartao_model_dump(self):
        """Testa que model_dump retorna dicionário correto."""
        cartao = Cartao(
            nomeTitular="João Silva",
            numero="4509953566233704",
            validade="2030-12-01",
            cvv="123"
        )
        data = cartao.model_dump()
        assert data == {
            "nomeTitular": "João Silva",
            "numero": "4509953566233704",
            "validade": "2030-12-01",
            "cvv": "123"
        }

