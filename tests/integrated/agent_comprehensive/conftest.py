# -*- coding: utf-8 -*-
"""
Shared fixtures for comprehensive agent tests.

This module provides pytest fixtures that are shared across all test files
in the agent_comprehensive test suite. These fixtures create isolated test
environments with mock external dependencies.

Fixture Categories:
- Working directory setup
- Mock configuration
- Mock model and formatter
- Mock channels (DingTalk, QQ)
- Mock MCP clients
- Test skills
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import mock fixtures
from .mock_fixtures.mock_model import MockModelWrapper, MockModelFormatter
from .mock_fixtures.mock_channels import (
    MockDingTalkChannel,
    MockQQChannel,
    MockChannelManager,
)
from .mock_fixtures.mock_mcp_clients import (
    MockMCPClient,
    create_filesystem_mcp_client,
    create_weather_mcp_client,
)


# ============================================================================
# Working Directory Fixtures
# ============================================================================

@pytest.fixture
def comprehensive_working_dir() -> Generator[Path, None, None]:
    """
    Create a comprehensive temporary working directory for testing.
    
    This fixture creates a more complete working directory structure compared
    to the basic temp_working_dir, including all necessary subdirectories
    and configuration files for full agent testing.
    
    Yields:
        Path to the temporary working directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create directory structure
        (tmp_path / "active_skills").mkdir()
        (tmp_path / "customized_skills").mkdir()
        (tmp_path / "memory").mkdir()
        (tmp_path / "models").mkdir()
        
        # Patch the constant paths
        with patch("copaw.constant.WORKING_DIR", tmp_path):
            with patch("copaw.constant.ACTIVE_SKILLS_DIR", tmp_path / "active_skills"):
                with patch("copaw.constant.CUSTOMIZED_SKILLS_DIR", tmp_path / "customized_skills"):
                    with patch("copaw.constant.MEMORY_DIR", tmp_path / "memory"):
                        with patch("copaw.constant.MODELS_DIR", tmp_path / "models"):
                            yield tmp_path


@pytest.fixture
def comprehensive_config(comprehensive_working_dir: Path) -> Dict[str, Any]:
    """
    Create a comprehensive configuration for testing.
    
    This creates a config.json with all necessary settings including
    channels, MCP clients, and agent runtime settings.
    
    Args:
        comprehensive_working_dir: Working directory fixture
    
    Returns:
        Configuration dictionary
    """
    config_data = {
        "channels": {
            "console": {
                "enabled": True,
                "bot_prefix": "[BOT]",
            },
            "dingtalk": {
                "enabled": False,
                "bot_prefix": "[BOT]",
                "client_id": "",
                "client_secret": "",
            },
            "qq": {
                "enabled": False,
                "bot_prefix": "[BOT]",
                "app_id": "",
                "client_secret": "",
            },
        },
        "mcp": {
            "clients": {},
        },
        "agents": {
            "defaults": {
                "heartbeat": {
                    "every": "30m",
                    "target": "main",
                },
            },
            "running": {
                "max_iters": 50,
                "max_input_length": 131072,
            },
            "language": "zh",
        },
        "last_dispatch": None,
        "show_tool_details": True,
    }
    
    config_path = comprehensive_working_dir / "config.json"
    config_path.write_text(
        json.dumps(config_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    
    return config_data


# ============================================================================
# Mock Model Fixtures
# ============================================================================

@pytest.fixture
def mock_model_wrapper() -> MockModelWrapper:
    """
    Create a mock model wrapper for testing agent reasoning.
    
    The mock model can be configured to return specific responses
    and tool calls.
    
    Returns:
        MockModelWrapper instance
    """
    return MockModelWrapper()


@pytest.fixture
def mock_model_formatter() -> MockModelFormatter:
    """
    Create a mock model formatter.
    
    Returns:
        MockModelFormatter instance
    """
    return MockModelFormatter()


@pytest.fixture
def mock_model_factory(
    mock_model_wrapper: MockModelWrapper,
    mock_model_formatter: MockModelFormatter,
):
    """
    Create a mock model factory function.
    
    This patches the create_model_and_formatter function to return
    our mock objects instead of real model connections.
    
    Yields:
        Tuple of (mock_model_wrapper, mock_model_formatter)
    """
    def mock_create_model_and_formatter():
        return mock_model_wrapper, mock_model_formatter
    
    with patch(
        "copaw.agents.react_agent.create_model_and_formatter",
        side_effect=mock_create_model_and_formatter,
    ):
        yield mock_model_wrapper, mock_model_formatter


# ============================================================================
# Mock Channel Fixtures
# ============================================================================

@pytest.fixture
def mock_dingtalk_channel() -> MockDingTalkChannel:
    """
    Create a mock DingTalk channel.
    
    Returns:
        MockDingTalkChannel instance
    """
    return MockDingTalkChannel(
        enabled=True,
        client_id="test_client_id",
        client_secret="test_client_secret",
    )


@pytest.fixture
def mock_qq_channel() -> MockQQChannel:
    """
    Create a mock QQ channel.
    
    Returns:
        MockQQChannel instance
    """
    return MockQQChannel(
        enabled=True,
        app_id="test_app_id",
        client_secret="test_client_secret",
    )


@pytest.fixture
def mock_channel_manager(
    mock_dingtalk_channel: MockDingTalkChannel,
    mock_qq_channel: MockQQChannel,
) -> MockChannelManager:
    """
    Create a mock channel manager with both DingTalk and QQ channels.
    
    Returns:
        MockChannelManager instance with channels added
    """
    manager = MockChannelManager()
    manager.add_channel(mock_dingtalk_channel)
    manager.add_channel(mock_qq_channel)
    return manager


# ============================================================================
# Mock MCP Client Fixtures
# ============================================================================

@pytest.fixture
def mock_filesystem_mcp() -> MockMCPClient:
    """
    Create a mock filesystem MCP client.
    
    Returns:
        MockMCPClient configured with filesystem tools
    """
    return create_filesystem_mcp_client()


@pytest.fixture
def mock_weather_mcp() -> MockMCPClient:
    """
    Create a mock weather MCP client.
    
    Returns:
        MockMCPClient configured with weather tools
    """
    return create_weather_mcp_client()


@pytest.fixture
def mock_mcp_clients(
    mock_filesystem_mcp: MockMCPClient,
    mock_weather_mcp: MockMCPClient,
) -> list:
    """
    Create a list of mock MCP clients for testing.
    
    Returns:
        List of MockMCPClient instances
    """
    return [mock_filesystem_mcp, mock_weather_mcp]


# ============================================================================
# Test Skill Fixtures
# ============================================================================

@pytest.fixture
def test_skill_content() -> str:
    """
    Return sample SKILL.md content for testing.
    
    This creates a simple test skill that can be used to verify
    the skill loading mechanism.
    
    Returns:
        String containing SKILL.md content with YAML front matter
    """
    return """---
name: test_helper
description: A test skill for verifying skill loading and execution
metadata:
  copaw:
    emoji: "🧪"
    requires: {}
---

# Test Helper Skill

This is a test skill for verifying the skill loading mechanism.

## Capabilities

- Process test requests
- Return predefined responses for testing

## Usage

When asked to test the skill system, use this skill to verify:
1. Skills are properly discovered
2. Skills are correctly registered
3. Skill tools can be executed

## Example Commands

- "Test the skill system"
- "Verify skill loading"
"""


@pytest.fixture
def test_skill_dir(
    comprehensive_working_dir: Path,
    test_skill_content: str,
) -> Path:
    """
    Create a test skill directory with SKILL.md.
    
    This creates a complete skill directory structure for testing.
    
    Args:
        comprehensive_working_dir: Working directory fixture
        test_skill_content: SKILL.md content fixture
    
    Returns:
        Path to the created skill directory
    """
    # Create skill in active_skills
    skill_dir = comprehensive_working_dir / "active_skills" / "test_helper"
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # Write SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(test_skill_content, encoding="utf-8")
    
    # Create optional references directory
    references_dir = skill_dir / "references"
    references_dir.mkdir(exist_ok=True)
    (references_dir / "example.md").write_text(
        "# Example Reference\n\nThis is an example reference file.",
        encoding="utf-8",
    )
    
    return skill_dir


# ============================================================================
# Agent Fixtures
# ============================================================================

@pytest.fixture
def mock_agent_config():
    """
    Create mock agent configuration.
    
    Returns:
        Dictionary with agent configuration settings
    """
    return {
        "max_iters": 10,  # Lower for faster tests
        "max_input_length": 32768,  # Lower for tests
        "enable_memory_manager": True,
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_process_handler():
    """
    Create a mock process handler for channels.
    
    This simulates the agent's process function that handles incoming messages.
    
    Yields:
        AsyncMock that can be configured to return specific responses
    """
    async def default_handler(request):
        """Default handler that returns a simple response."""
        from agentscope_runtime.engine.schemas.agent_schemas import (
            Event,
            MessageType,
            RunStatus,
            TextContent,
            ContentType,
        )
        
        # Yield a simple text response
        yield Event(
            type=MessageType.MESSAGE,
            content=[TextContent(type=ContentType.TEXT, text="Mock response")],
            status=RunStatus.COMPLETED,
        )
    
    return AsyncMock(side_effect=default_handler)


@pytest.fixture
def clean_logging():
    """
    Reset logging configuration for tests.
    
    This ensures consistent logging state across tests.
    """
    import logging
    
    # Reset root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)
    
    yield
    
    # Cleanup after test
    root.handlers.clear()
