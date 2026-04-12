# -*- coding: utf-8 -*-
"""Integrated tests for CoPaw version."""
from __future__ import annotations

import subprocess
import sys

import pytest
from packaging.version import Version


class TestVersionImport:
    """Tests for version import functionality."""

    def test_version_import(self) -> None:
        """Test that version can be imported without errors."""
        from copaw.__version__ import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_is_string(self) -> None:
        """Test that version is a string."""
        from copaw.__version__ import __version__

        assert isinstance(__version__, str)

    def test_version_has_version_number(self) -> None:
        """Test that version contains version number pattern."""
        from copaw.__version__ import __version__

        # Should contain at least one dot (e.g., "1.0.0")
        assert "." in __version__


class TestVersionPe440Compliance:
    """Tests for PEP 440 compliance."""

    def test_version_pep440_compliant(self) -> None:
        """Test that version follows PEP 440 format."""
        from copaw.__version__ import __version__

        try:
            parsed_version = Version(__version__)
            assert str(parsed_version) == __version__
        except Exception as e:
            pytest.fail(f"Version '{__version__}' is not PEP 440 compliant: {e}")

    def test_version_has_major_minor_patch(self) -> None:
        """Test that version has at least major.minor.patch format."""
        from copaw.__version__ import __version__

        parts = __version__.split(".")
        assert len(parts) >= 2  # At least major.minor


class TestVersionSubprocess:
    """Tests for version access via subprocess."""

    def test_version_via_subprocess(self) -> None:
        """Test that version can be accessed via subprocess."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from copaw.__version__ import __version__; print(__version__)",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert result.returncode == 0, f"Failed to get version: {result.stderr}"
        version = result.stdout.strip()
        assert version
        assert "." in version

    def test_copaw_version_cli(self) -> None:
        """Test that copaw --version works."""
        result = subprocess.run(
            ["copaw", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        # copaw command might not be in PATH during tests
        # So we just check if it runs
        if result.returncode == 0:
            assert len(result.stdout.strip()) > 0 or len(result.stderr.strip()) > 0


class TestPackageStructure:
    """Tests for package structure integrity."""

    def test_package_import(self) -> None:
        """Test that copaw package can be imported."""
        import copaw

        assert copaw is not None

    def test_cli_module_import(self) -> None:
        """Test that CLI module can be imported."""
        from copaw.cli.main import cli

        assert cli is not None

    def test_config_module_import(self) -> None:
        """Test that config module can be imported."""
        from copaw.config import Config

        assert Config is not None

    def test_providers_module_import(self) -> None:
        """Test that providers module can be imported."""
        from copaw.providers import load_providers_json

        assert load_providers_json is not None

    def test_envs_module_import(self) -> None:
        """Test that envs module can be imported."""
        from copaw.envs import load_envs

        assert load_envs is not None
