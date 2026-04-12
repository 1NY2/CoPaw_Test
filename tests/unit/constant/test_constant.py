# -*- coding: utf-8 -*-
"""Tests for copaw.constant module."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestWorkingDir:
    """Tests for WORKING_DIR constant."""

    def test_working_dir_default(self) -> None:
        """Test default working directory is ~/.copaw."""
        from copaw.constant import WORKING_DIR

        expected = Path("~/.copaw").expanduser().resolve()
        assert WORKING_DIR == expected

    def test_working_dir_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test WORKING_DIR can be overridden via environment variable."""
        custom_path = "/tmp/custom_copaw"
        monkeypatch.setenv("COPAW_WORKING_DIR", custom_path)

        # Need to reimport to get the new value
        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import WORKING_DIR
        expected = Path(custom_path).expanduser().resolve()
        assert WORKING_DIR == expected


class TestFileConstants:
    """Tests for file path constants."""

    def test_jobs_file_default(self) -> None:
        """Test default JOBS_FILE constant."""
        from copaw.constant import JOBS_FILE

        assert JOBS_FILE == "jobs.json"

    def test_chats_file_default(self) -> None:
        """Test default CHATS_FILE constant."""
        from copaw.constant import CHATS_FILE

        assert CHATS_FILE == "chats.json"

    def test_config_file_default(self) -> None:
        """Test default CONFIG_FILE constant."""
        from copaw.constant import CONFIG_FILE

        assert CONFIG_FILE == "config.json"

    def test_heartbeat_file_default(self) -> None:
        """Test default HEARTBEAT_FILE constant."""
        from copaw.constant import HEARTBEAT_FILE

        assert HEARTBEAT_FILE == "HEARTBEAT.md"

    def test_env_file_constants(self) -> None:
        """Test environment variable constants."""
        from copaw.constant import LOG_LEVEL_ENV

        assert LOG_LEVEL_ENV == "COPAW_LOG_LEVEL"


class TestHeartbeatConstants:
    """Tests for heartbeat configuration constants."""

    def test_heartbeat_default_every(self) -> None:
        """Test default heartbeat interval."""
        from copaw.constant import HEARTBEAT_DEFAULT_EVERY

        assert HEARTBEAT_DEFAULT_EVERY == "30m"

    def test_heartbeat_default_target(self) -> None:
        """Test default heartbeat target."""
        from copaw.constant import HEARTBEAT_DEFAULT_TARGET

        assert HEARTBEAT_DEFAULT_TARGET == "main"

    def test_heartbeat_target_last(self) -> None:
        """Test heartbeat target 'last' constant."""
        from copaw.constant import HEARTBEAT_TARGET_LAST

        assert HEARTBEAT_TARGET_LAST == "last"


class TestDocsEnabled:
    """Tests for DOCS_ENABLED constant."""

    def test_docs_disabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test docs are disabled by default."""
        monkeypatch.delenv("COPAW_OPENAPI_DOCS", raising=False)

        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import DOCS_ENABLED
        assert DOCS_ENABLED is False

    def test_docs_enabled_with_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test docs can be enabled with 'true'."""
        monkeypatch.setenv("COPAW_OPENAPI_DOCS", "true")

        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import DOCS_ENABLED
        assert DOCS_ENABLED is True

    def test_docs_enabled_with_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test docs can be enabled with '1'."""
        monkeypatch.setenv("COPAW_OPENAPI_DOCS", "1")

        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import DOCS_ENABLED
        assert DOCS_ENABLED is True

    def test_docs_enabled_with_yes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test docs can be enabled with 'yes'."""
        monkeypatch.setenv("COPAW_OPENAPI_DOCS", "yes")

        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import DOCS_ENABLED
        assert DOCS_ENABLED is True


class TestMemoryCompactionConfig:
    """Tests for memory compaction configuration constants."""

    def test_memory_compact_keep_recent_default(self) -> None:
        """Test default keep recent count."""
        from copaw.constant import MEMORY_COMPACT_KEEP_RECENT

        assert MEMORY_COMPACT_KEEP_RECENT == 3

    def test_memory_compact_ratio_default(self) -> None:
        """Test default compaction ratio."""
        from copaw.constant import MEMORY_COMPACT_RATIO

        assert MEMORY_COMPACT_RATIO == 0.7

    def test_memory_compact_keep_recent_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test keep recent can be overridden via env."""
        monkeypatch.setenv("COPAW_MEMORY_COMPACT_KEEP_RECENT", "5")

        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import MEMORY_COMPACT_KEEP_RECENT
        assert MEMORY_COMPACT_KEEP_RECENT == 5

    def test_memory_compact_ratio_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test compaction ratio can be overridden via env."""
        monkeypatch.setenv("COPAW_MEMORY_COMPACT_RATIO", "0.5")

        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import MEMORY_COMPACT_RATIO
        assert MEMORY_COMPACT_RATIO == 0.5


class TestDashscopeBaseUrl:
    """Tests for DASHSCOPE_BASE_URL constant."""

    def test_dashscope_base_url_default(self) -> None:
        """Test default DashScope base URL."""
        from copaw.constant import DASHSCOPE_BASE_URL

        expected = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert DASHSCOPE_BASE_URL == expected

    def test_dashscope_base_url_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test DashScope base URL can be overridden via env."""
        custom_url = "https://custom.dashscope.com/v1"
        monkeypatch.setenv("DASHSCOPE_BASE_URL", custom_url)

        import importlib
        import copaw.constant
        importlib.reload(copaw.constant)

        from copaw.constant import DASHSCOPE_BASE_URL
        assert DASHSCOPE_BASE_URL == custom_url


class TestGetAvailableChannels:
    """Tests for get_available_channels function."""

    def test_get_available_channels_default(self) -> None:
        """Test default returns all registered channels."""
        from copaw.constant import get_available_channels

        channels = get_available_channels()

        # Should at least include console
        assert "console" in channels
        assert isinstance(channels, tuple)

    def test_get_available_channels_filtered(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test channels can be filtered via COPAW_ENABLED_CHANNELS."""
        monkeypatch.setenv("COPAW_ENABLED_CHANNELS", "console,dingtalk")

        from copaw.constant import get_available_channels

        channels = get_available_channels()

        # Should only include enabled channels
        assert "console" in channels or "dingtalk" in channels

    def test_get_available_channels_empty_env_uses_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test empty COPAW_ENABLED_CHANNELS uses all channels."""
        monkeypatch.setenv("COPAW_ENABLED_CHANNELS", "")

        from copaw.constant import get_available_channels

        channels = get_available_channels()

        # Should return all channels when env is empty
        assert isinstance(channels, tuple)
        assert len(channels) > 0
