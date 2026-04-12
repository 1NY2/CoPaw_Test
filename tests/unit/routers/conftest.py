# -*- coding: utf-8 -*-
"""Fixtures for API Routers tests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for the API.

    Yields:
        TestClient instance
    """
    from copaw.app._app import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_config_for_routers(temp_working_dir: Path) -> dict:
    """Create a mock config for router testing.

    Args:
        temp_working_dir: Temporary working directory fixture

    Returns:
        Dictionary containing the mock config
    """
    config_data = {
        "channels": {
            "console": {"enabled": True, "bot_prefix": "[BOT]"},
            "imessage": {"enabled": False, "bot_prefix": "", "db_path": "~/Library/Messages/chat.db", "poll_sec": 1.0},
            "discord": {"enabled": False, "bot_prefix": "", "bot_token": "", "http_proxy": "", "http_proxy_auth": ""},
        },
        "mcp": {
            "clients": {}
        },
        "agents": {
            "defaults": {
                "heartbeat": {
                    "every": "30m",
                    "target": "main"
                }
            },
            "running": {
                "max_iters": 50,
                "max_input_length": 131072
            }
        }
    }

    config_path = temp_working_dir / "config.json"
    config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    return config_data


@pytest.fixture
def mock_envs_for_routers(temp_working_dir: Path) -> dict:
    """Create mock environment variables for router testing.

    Args:
        temp_working_dir: Temporary working directory fixture

    Returns:
        Dictionary containing mock environment variables
    """
    envs_data = {
        "TEST_VAR": "test_value",
        "API_KEY": "sk-test-12345"
    }

    envs_path = temp_working_dir / "envs.json"
    envs_path.write_text(json.dumps(envs_data, indent=2), encoding="utf-8")

    return envs_data
