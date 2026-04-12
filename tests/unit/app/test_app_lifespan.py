# -*- coding: utf-8 -*-
"""Tests for App module lifespan and basic functionality."""
from __future__ import annotations

from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient


class TestAppCreation:
    """Tests for FastAPI app creation."""

    def test_app_instance_exists(self) -> None:
        """Test that the app instance is created."""
        from copaw.app._app import app

        assert app is not None
        # App should have routes
        assert len(app.routes) > 0

    def test_app_has_version_endpoint(self) -> None:
        """Test that app has /api/version endpoint."""
        from copaw.app._app import app

        client = TestClient(app)

        response = client.get("/api/version")

        assert response.status_code == 200
        assert "version" in response.json()

    def test_app_has_root_endpoint(self) -> None:
        """Test that app has root endpoint."""
        from copaw.app._app import app

        client = TestClient(app)

        response = client.get("/")

        # Root endpoint should return something
        assert response.status_code == 200

    def test_app_has_routes(self) -> None:
        """Test that app has routes."""
        from copaw.app._app import app

        # App should have routes
        assert len(app.routes) > 0


class TestAppRoutes:
    """Tests for app routes."""

    def test_api_router_included(self) -> None:
        """Test that API router is included."""
        from copaw.app._app import app

        routes = [route.path for route in app.routes]
        
        # Check that API routes are included
        api_routes = [r for r in routes if r.startswith("/api/")]
        assert len(api_routes) > 0

    def test_agent_router_included(self) -> None:
        """Test that agent router is included."""
        from copaw.app._app import app

        routes = [route.path for route in app.routes]
        
        # Check for agent routes
        agent_routes = [r for r in routes if "/agent" in r]
        assert len(agent_routes) > 0


class TestConsoleStaticDir:
    """Tests for console static directory resolution."""

    def test_resolve_console_static_dir_from_env(
        self, temp_working_dir: Path
    ) -> None:
        """Test resolving console static dir from environment variable."""
        import os
        
        console_dir = temp_working_dir / "custom_console"
        console_dir.mkdir(parents=True, exist_ok=True)
        (console_dir / "index.html").write_text("test", encoding="utf-8")

        with patch.dict(os.environ, {"COPAW_CONSOLE_STATIC_DIR": str(console_dir)}):
            # Re-import to get updated value
            from copaw.app._app import _resolve_console_static_dir
            
            result = _resolve_console_static_dir()
            assert result == str(console_dir)

    def test_resolve_console_static_dir_not_exists(self) -> None:
        """Test resolving console static dir when it doesn't exist."""
        from copaw.app._app import _resolve_console_static_dir
        
        result = _resolve_console_static_dir()
        # Should return some path (either found or fallback)
        assert isinstance(result, str)


class TestAppVersion:
    """Tests for version endpoint."""

    def test_version_returns_correct_format(self) -> None:
        """Test that version endpoint returns correct format."""
        from copaw.app._app import app
        from copaw.__version__ import __version__

        client = TestClient(app)

        response = client.get("/api/version")

        assert response.status_code == 200
        data = response.json()
        assert data["version"] == __version__


class TestAppLifespanComponents:
    """Tests for app lifespan component initialization."""

    def test_runner_exists(self) -> None:
        """Test that AgentRunner instance exists."""
        from copaw.app._app import runner

        assert runner is not None

    def test_agent_app_exists(self) -> None:
        """Test that AgentApp instance exists."""
        from copaw.app._app import agent_app

        assert agent_app is not None
        # AgentApp has internal runner attribute
        assert hasattr(agent_app, "_runner") or hasattr(agent_app, "router")
