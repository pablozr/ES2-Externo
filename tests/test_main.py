import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestMain:
    """Testes para o módulo main."""

    def test_app_startup(self):
        """Testa que a aplicação inicia corretamente."""
        with patch("functions.database.asyncpg_manager.asyncpg_manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            from main import app
            
            assert app is not None

    def test_app_has_cors_middleware(self):
        """Testa que a aplicação tem middleware CORS configurado."""
        with patch("functions.database.asyncpg_manager.asyncpg_manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            from main import app
            
            middleware_classes = [m.cls.__name__ for m in app.user_middleware]
            assert "CORSMiddleware" in middleware_classes

    def test_app_includes_email_router(self):
        """Testa que a aplicação inclui o router de email."""
        with patch("functions.database.asyncpg_manager.asyncpg_manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            from main import app
            
            routes = [route.path for route in app.routes]
            assert "/enviarEmail" in routes

    def test_app_includes_cartao_router(self):
        """Testa que a aplicação inclui o router de cartão."""
        with patch("functions.database.asyncpg_manager.asyncpg_manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            from main import app
            
            routes = [route.path for route in app.routes]
            assert "/validaCartaoDeCredito" in routes

    def test_app_includes_cobranca_router(self):
        """Testa que a aplicação inclui o router de cobrança."""
        with patch("functions.database.asyncpg_manager.asyncpg_manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            from main import app
            
            routes = [route.path for route in app.routes]
            assert "/cobranca" in routes
            assert "/cobranca/{cobranca_id}" in routes
            assert "/filaCobranca" in routes
            assert "/processaCobrancasEmFila" in routes


class TestLifespan:
    """Testes para o ciclo de vida da aplicação."""

    @pytest.mark.asyncio
    async def test_lifespan_connect_and_disconnect(self):
        """Testa que o lifespan conecta e desconecta corretamente."""
        with patch("main.asyncpg_manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = AsyncMock()
            
            from main import lifespan, app
            
            async with lifespan(app):
                mock_manager.connect.assert_called_once()
            
            mock_manager.disconnect.assert_called_once()

