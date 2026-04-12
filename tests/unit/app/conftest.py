# -*- coding: utf-8 -*-
"""Fixtures for App module tests."""
from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def mock_console_static_dir(temp_working_dir: Path) -> Generator[Path, None, None]:
    """Create a mock console static directory.

    Args:
        temp_working_dir: Temporary working directory fixture

    Yields:
        Path to the mock console static directory
    """
    console_dir = temp_working_dir / "console"
    console_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal index.html
    (console_dir / "index.html").write_text(
        "<!DOCTYPE html><html><body>Test Console</body></html>",
        encoding="utf-8"
    )
    
    # Create assets directory
    assets_dir = console_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    yield console_dir


@pytest.fixture
def mock_config_for_app(temp_working_dir: Path) -> dict:
    """Create a mock config for app testing.

    Args:
        temp_working_dir: Temporary working directory fixture

    Returns:
        Dictionary containing the mock config
    """
    import json
    
    config_data = {
        "channels": {
            "console": {"enabled": True, "bot_prefix": "[BOT]"},
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
    config_path.write_text(json.dumps(config_data), encoding="utf-8")
    
    return config_data
