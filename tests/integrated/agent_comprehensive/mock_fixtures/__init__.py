# -*- coding: utf-8 -*-
"""
Mock fixtures for comprehensive agent tests.

This package contains mock objects that simulate external services:
- mock_model: Mock LLM model that returns predefined responses
- mock_channels: Mock DingTalk/QQ channels for message processing tests
- mock_mcp_clients: Mock MCP clients for tool integration tests

These mocks allow tests to run without real external service connections.
"""

from .mock_model import MockModelWrapper, create_mock_model_response
from .mock_channels import MockDingTalkChannel, MockQQChannel, MockChannelManager
from .mock_mcp_clients import MockMCPClient, MockMCPTool

__all__ = [
    "MockModelWrapper",
    "create_mock_model_response",
    "MockDingTalkChannel",
    "MockQQChannel",
    "MockChannelManager",
    "MockMCPClient",
    "MockMCPTool",
]
