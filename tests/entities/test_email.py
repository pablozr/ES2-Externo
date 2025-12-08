import pytest
from pydantic import ValidationError

from entities.email.email import Email, EmailRequest


class TestEmail:
    """Testes para a entidade Email."""

    def test_email_valido(self):
        """Testa criação de email com dados válidos."""
        email = Email(
            id=1,
            email="test@example.com",
            assunto="Teste",
            mensagem="Mensagem de teste"
        )
        assert email.id == 1
        assert email.email == "test@example.com"
        assert email.assunto == "Teste"
        assert email.mensagem == "Mensagem de teste"

    def test_email_formato_invalido(self):
        """Testa que email com formato inválido falha."""
        with pytest.raises(ValidationError):
            Email(
                id=1,
                email="invalid-email",
                assunto="Teste",
                mensagem="Mensagem"
            )

    def test_email_sem_arroba(self):
        """Testa que email sem @ falha."""
        with pytest.raises(ValidationError):
            Email(
                id=1,
                email="testexample.com",
                assunto="Teste",
                mensagem="Mensagem"
            )

    def test_email_sem_id(self):
        """Testa que email sem ID falha."""
        with pytest.raises(ValidationError):
            Email(
                email="test@example.com",
                assunto="Teste",
                mensagem="Mensagem"
            )

    def test_email_sem_assunto(self):
        """Testa que email sem assunto falha."""
        with pytest.raises(ValidationError):
            Email(
                id=1,
                email="test@example.com",
                mensagem="Mensagem"
            )

    def test_email_sem_mensagem(self):
        """Testa que email sem mensagem falha."""
        with pytest.raises(ValidationError):
            Email(
                id=1,
                email="test@example.com",
                assunto="Teste"
            )

    def test_email_model_dump(self):
        """Testa que model_dump retorna dicionário correto."""
        email = Email(
            id=1,
            email="test@example.com",
            assunto="Teste",
            mensagem="Mensagem"
        )
        data = email.model_dump()
        assert data == {
            "id": 1,
            "email": "test@example.com",
            "assunto": "Teste",
            "mensagem": "Mensagem"
        }


class TestEmailRequest:
    """Testes para a entidade EmailRequest."""

    def test_email_request_valido(self):
        """Testa criação de EmailRequest com dados válidos."""
        email_request = EmailRequest(
            email="test@example.com",
            assunto="Teste",
            mensagem="Mensagem de teste"
        )
        assert email_request.email == "test@example.com"
        assert email_request.assunto == "Teste"
        assert email_request.mensagem == "Mensagem de teste"

    def test_email_request_formato_invalido(self):
        """Testa que EmailRequest com email inválido falha."""
        with pytest.raises(ValidationError):
            EmailRequest(
                email="invalid",
                assunto="Teste",
                mensagem="Mensagem"
            )

    def test_email_request_sem_email(self):
        """Testa que EmailRequest sem email falha."""
        with pytest.raises(ValidationError):
            EmailRequest(
                assunto="Teste",
                mensagem="Mensagem"
            )

    def test_email_request_sem_assunto(self):
        """Testa que EmailRequest sem assunto falha."""
        with pytest.raises(ValidationError):
            EmailRequest(
                email="test@example.com",
                mensagem="Mensagem"
            )

    def test_email_request_sem_mensagem(self):
        """Testa que EmailRequest sem mensagem falha."""
        with pytest.raises(ValidationError):
            EmailRequest(
                email="test@example.com",
                assunto="Teste"
            )

    def test_email_request_model_dump(self):
        """Testa que model_dump retorna dicionário correto."""
        email_request = EmailRequest(
            email="test@example.com",
            assunto="Assunto Teste",
            mensagem="Corpo da mensagem"
        )
        data = email_request.model_dump()
        assert data == {
            "email": "test@example.com",
            "assunto": "Assunto Teste",
            "mensagem": "Corpo da mensagem"
        }

    def test_email_request_email_com_subdominio(self):
        """Testa EmailRequest com email contendo subdomínio."""
        email_request = EmailRequest(
            email="user@mail.example.com",
            assunto="Teste",
            mensagem="Mensagem"
        )
        assert email_request.email == "user@mail.example.com"

    def test_email_request_email_com_numeros(self):
        """Testa EmailRequest com email contendo números."""
        email_request = EmailRequest(
            email="user123@example.com",
            assunto="Teste",
            mensagem="Mensagem"
        )
        assert email_request.email == "user123@example.com"

    def test_email_request_assunto_longo(self):
        """Testa EmailRequest com assunto longo."""
        assunto_longo = "A" * 500
        email_request = EmailRequest(
            email="test@example.com",
            assunto=assunto_longo,
            mensagem="Mensagem"
        )
        assert len(email_request.assunto) == 500

    def test_email_request_mensagem_longa(self):
        """Testa EmailRequest com mensagem longa."""
        mensagem_longa = "B" * 10000
        email_request = EmailRequest(
            email="test@example.com",
            assunto="Teste",
            mensagem=mensagem_longa
        )
        assert len(email_request.mensagem) == 10000

