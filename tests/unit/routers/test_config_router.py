# -*- coding: utf-8 -*-
"""Tests for config router."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


class TestConfigRouter:
    """Tests for config router endpoints."""

    def test_list_channel_types(self, test_client: TestClient) -> None:
        """Test listing channel types."""
        response = test_client.get("/api/config/channels/types")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "console" in data

    def test_list_channels(self, test_client: TestClient) -> None:
        """Test listing channels."""
        response = test_client.get("/api/config/channels")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_channel(self, test_client: TestClient) -> None:
        """Test getting a specific channel."""
        response = test_client.get("/api/config/channels/console")

        assert response.status_code == 200
        data = response.json()
        # Should have some channel config
        assert isinstance(data, dict)

    def test_get_channel_not_found(self, test_client: TestClient) -> None:
        """Test getting a non-existent channel."""
        response = test_client.get("/api/config/channels/nonexistent_channel_xyz")

        assert response.status_code == 404

    def test_put_channel(self, test_client: TestClient) -> None:
        """Test updating a channel config."""
        new_config = {
            "enabled": True,
            "bot_prefix": "[TEST]"
        }

        response = test_client.put(
            "/api/config/channels/console",
            json=new_config
        )

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["bot_prefix"] == "[TEST]"

    def test_put_channel_not_found(self, test_client: TestClient) -> None:
        """Test updating a non-existent channel."""
        new_config = {
            "enabled": True,
            "bot_prefix": "[TEST]"
        }

        response = test_client.put(
            "/api/config/channels/nonexistent_channel_xyz",
            json=new_config
        )

        assert response.status_code == 404
