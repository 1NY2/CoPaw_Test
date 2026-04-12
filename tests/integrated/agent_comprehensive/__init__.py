# -*- coding: utf-8 -*-
"""
Comprehensive Agent Test Suite.

This module provides a comprehensive test suite for validating the CoPaw agent's
core functionality including skills loading, MCP tool integration, channel
message processing, and agent reasoning mechanisms.

The test suite uses mock objects to simulate external services (DingTalk, QQ, MCP
servers, LLM APIs) making tests independent, reproducible, and fast.

Key Components:
- Mock fixtures for isolating tests from external dependencies
- Test skills for validating the skills loading mechanism
- Comprehensive test cases covering all major agent workflows

Usage:
    pytest tests/integrated/agent_comprehensive/ -v
"""
