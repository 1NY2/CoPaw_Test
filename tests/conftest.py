# -*- coding: utf-8 -*-
"""
Global fixtures and configuration for CoPaw tests.

This module provides shared fixtures that can be used across all test files.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_working_dir() -> Generator[Path, None, None]:
    """Create a temporary working directory for testing.

    This fixture:
    - Creates a temporary directory
    - Patches copaw.constant.WORKING_DIR to point to it
    - Yields the path for use in tests
    - Cleans up after the test

    Yields:
        Path to the temporary working directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with patch("copaw.constant.WORKING_DIR", tmp_path):
            # Also patch the derived paths
            with patch("copaw.constant.ACTIVE_SKILLS_DIR", tmp_path / "active_skills"):
                with patch("copaw.constant.CUSTOMIZED_SKILLS_DIR", tmp_path / "customized_skills"):
                    with patch("copaw.constant.CUSTOM_CHANNELS_DIR", tmp_path / "custom_channels"):
                        with patch("copaw.constant.MODELS_DIR", tmp_path / "models"):
                            with patch("copaw.constant.MEMORY_DIR", tmp_path / "memory"):
                                yield tmp_path


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary config directory for testing.

    Yields:
        Path to the temporary config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        yield tmp_path


@pytest.fixture
def mock_config(temp_working_dir: Path) -> dict:
    """Create a mock configuration and write to temp working dir.

    Args:
        temp_working_dir: Temporary working directory fixture

    Returns:
        Dictionary containing the mock configuration
    """
    config_data = {
        "channels": {
            "console": {"enabled": True, "bot_prefix": "[BOT]"},
            "imessage": {"enabled": False, "bot_prefix": "", "db_path": "~/Library/Messages/chat.db", "poll_sec": 1.0},
            "discord": {"enabled": False, "bot_prefix": "", "bot_token": "", "http_proxy": "", "http_proxy_auth": ""},
            "dingtalk": {"enabled": False, "bot_prefix": "", "client_id": "", "client_secret": "", "media_dir": "~/.copaw/media"},
            "feishu": {"enabled": False, "bot_prefix": "", "app_id": "", "app_secret": "", "encrypt_key": "", "verification_token": "", "media_dir": "~/.copaw/media"},
            "qq": {"enabled": False, "bot_prefix": "", "app_id": "", "client_secret": ""},
        },
        "mcp": {
            "clients": {}
        },
        "last_api": {"host": None, "port": None},
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
            },
            "language": "zh",
            "installed_md_files_language": None
        },
        "last_dispatch": None,
        "show_tool_details": True
    }

    config_path = temp_working_dir / "config.json"
    config_path.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return config_data


@pytest.fixture
def mock_providers_json(temp_config_dir: Path) -> dict:
    """Create a mock providers.json file.

    Args:
        temp_config_dir: Temporary config directory fixture

    Returns:
        Dictionary containing the mock providers configuration
    """
    providers_data = {
        "providers": {
            "openai": {
                "api_key": "",
                "base_url": "https://api.openai.com/v1",
                "extra_models": []
            },
            "anthropic": {
                "api_key": "",
                "base_url": "https://api.anthropic.com",
                "extra_models": []
            },
            "dashscope": {
                "api_key": "",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "extra_models": []
            }
        },
        "custom_providers": {},
        "active_llm": {
            "provider_id": "",
            "model": ""
        }
    }

    providers_path = temp_config_dir / "providers.json"
    providers_path.write_text(json.dumps(providers_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return providers_data


@pytest.fixture
def mock_envs_json(temp_config_dir: Path) -> dict:
    """Create a mock envs.json file.

    Args:
        temp_config_dir: Temporary config directory fixture

    Returns:
        Dictionary containing the mock environment variables
    """
    envs_data = {
        "OPENAI_API_KEY": "sk-test-key-12345",
        "ANTHROPIC_API_KEY": "sk-ant-test-12345",
        "TAVILY_API_KEY": "tvly-test-12345"
    }

    envs_path = temp_config_dir / "envs.json"
    envs_path.write_text(json.dumps(envs_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return envs_data


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Set mock environment variables.

    Args:
        monkeypatch: pytest monkeypatch fixture

    Returns:
        Dictionary containing the mock environment variables
    """
    env_vars = {
        "COPAW_WORKING_DIR": "",
        "COPAW_LOG_LEVEL": "info",
        "COPAW_OPENAPI_DOCS": "false"
    }

    for key, value in env_vars.items():
        if value:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture
def clean_os_environ() -> Generator[dict, None, None]:
    """Provide a clean os.environ for testing.

    Saves current environment, yields a clean one, and restores after test.

    Yields:
        Dictionary containing the clean environment
    """
    # Save current environment
    old_environ = os.environ.copy()

    # Clear and set minimal environment
    os.environ.clear()
    os.environ.update({
        "PATH": old_environ.get("PATH", ""),
        "HOME": old_environ.get("HOME", ""),
        "USER": old_environ.get("USER", ""),
    })

    yield os.environ

    # Restore original environment
    os.environ.clear()
    os.environ.update(old_environ)


@pytest.fixture
def mock_builtin_skills(temp_working_dir: Path) -> Path:
    """Create mock builtin skills directory structure.

    Args:
        temp_working_dir: Temporary working directory fixture

    Returns:
        Path to the mock builtin skills directory
    """
    # This is just for reference - actual skills are in src/copaw/agents/skills/
    # Tests should use the actual builtin skills
    return Path(__file__).parent.parent / "src" / "copaw" / "agents" / "skills"


@pytest.fixture
def sample_skill_md() -> str:
    """Return sample SKILL.md content for testing.

    Returns:
        String containing sample SKILL.md content with YAML front matter
    """
    return """---
name: test_skill
description: A test skill for unit testing
---

# Test Skill

This is a test skill for unit testing purposes.

## Usage

- Step 1: Do something
- Step 2: Do another thing
"""


@pytest.fixture
def mock_http_response():
    """Factory fixture for creating mock HTTP responses.

    Returns:
        A function that creates mock responses
    """
    def _create_response(
        status_code: int = 200,
        json_data: dict | None = None,
        text: str = ""
    ):
        class MockResponse:
            def __init__(self):
                self.status_code = status_code
                self._json_data = json_data or {}
                self.text = text

            def json(self):
                return self._json_data

            def raise_for_status(self):
                if status_code >= 400:
                    raise Exception(f"HTTP {status_code}")

        return MockResponse()

    return _create_response


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner.

    Returns:
        Click CliRunner instance
    """
    from click.testing import CliRunner
    return CliRunner()


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_network: marks tests that require network access"
    )
