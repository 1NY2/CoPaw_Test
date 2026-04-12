# -*- coding: utf-8 -*-
"""
Shared fixtures and configuration for provider tests.
"""
import json
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    """Create a temporary config directory for testing."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_provider_settings() -> dict:
    """Return sample provider settings."""
    return {
        "api_key": "sk-test-api-key",
        "base_url": "https://api.test.com/v1",
        "extra_models": []
    }


@pytest.fixture
def sample_providers_json() -> dict:
    """Return sample providers.json data."""
    return {
        "providers": {
            "openai": {
                "api_key": "sk-test-openai",
                "base_url": "https://api.openai.com/v1",
                "extra_models": []
            },
            "anthropic": {
                "api_key": "sk-test-anthropic",
                "base_url": "https://api.anthropic.com",
                "extra_models": []
            }
        },
        "custom_providers": {},
        "active_llm": {
            "provider_id": "openai",
            "model": "gpt-4"
        }
    }
