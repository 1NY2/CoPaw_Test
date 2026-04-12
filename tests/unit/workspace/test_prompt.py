# -*- coding: utf-8 -*-
"""Tests for agent identity in system prompt."""
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

# NOTE: build_system_prompt_from_working_dir() signature has changed.
# It no longer accepts working_dir and agent_id parameters.
# Tests are updated to mock copaw.constant.WORKING_DIR instead.


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace


def test_prompt_with_agents_md(temp_workspace):  # pylint: disable=W0621
    """Test system prompt with AGENTS.md file."""
    from copaw.agents.prompt import build_system_prompt_from_working_dir

    # Create a simple AGENTS.md
    agents_md = temp_workspace / "AGENTS.md"
    agents_md.write_text("You are a helpful assistant.", encoding="utf-8")

    # Mock WORKING_DIR in the constant module
    with patch("copaw.constant.WORKING_DIR", temp_workspace):
        prompt = build_system_prompt_from_working_dir()

    assert "You are a helpful assistant" in prompt


def test_prompt_with_multiple_md_files(temp_workspace):  # pylint: disable=W0621
    """Test system prompt combines multiple markdown files."""
    from copaw.agents.prompt import build_system_prompt_from_working_dir

    # Create AGENTS.md
    agents_md = temp_workspace / "AGENTS.md"
    agents_md.write_text("# Agents Rules\n\nYou are a helpful assistant.", encoding="utf-8")

    # Create SOUL.md
    soul_md = temp_workspace / "SOUL.md"
    soul_md.write_text("# Soul\n\nBe kind and helpful.", encoding="utf-8")

    with patch("copaw.constant.WORKING_DIR", temp_workspace):
        prompt = build_system_prompt_from_working_dir()

    assert "Agents Rules" in prompt
    assert "Soul" in prompt
    assert "Be kind and helpful" in prompt


def test_prompt_with_empty_workspace(temp_workspace):  # pylint: disable=W0621
    """Test system prompt with empty workspace."""
    from copaw.agents.prompt import build_system_prompt_from_working_dir

    with patch("copaw.constant.WORKING_DIR", temp_workspace):
        prompt = build_system_prompt_from_working_dir()

    # Should return some default content even with no files
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_prompt_structure(temp_workspace):  # pylint: disable=W0621
    """Test the structure of generated prompt."""
    from copaw.agents.prompt import build_system_prompt_from_working_dir

    agents_md = temp_workspace / "AGENTS.md"
    agents_md.write_text("Test content", encoding="utf-8")

    with patch("copaw.constant.WORKING_DIR", temp_workspace):
        prompt = build_system_prompt_from_working_dir()

    # Should be a valid string
    assert isinstance(prompt, str)
    assert len(prompt) > 0
