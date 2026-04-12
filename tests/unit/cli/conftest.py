# -*- coding: utf-8 -*-
"""
Shared fixtures and configuration for CLI tests.
"""
import pytest
from pathlib import Path
from typing import Generator


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_working_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a mock working directory for CLI tests."""
    working_dir = tmp_path / ".copaw"
    working_dir.mkdir()
    yield working_dir
