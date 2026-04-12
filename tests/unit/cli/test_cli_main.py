# -*- coding: utf-8 -*-
"""Tests for CLI main module."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import click
from click.testing import CliRunner

from copaw.__version__ import __version__
from copaw.cli.main import cli


class TestCliMain:
    """Tests for CLI main entry point."""

    def test_cli_help_option(self, cli_runner: CliRunner) -> None:
        """Test that help option works."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output

    def test_cli_version_option(self, cli_runner: CliRunner) -> None:
        """Test that version option works."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_cli_host_port_options_passed_to_subcommand(
        self, cli_runner: CliRunner
    ) -> None:
        """Test --host and --port options are passed to subcommands."""
        with patch("copaw.cli.main.read_last_api", return_value=None):
            # Create a test command to verify options are passed
            @cli.command("test-host-port")
            @click.pass_context
            def test_host_port(ctx):
                click.echo(f"host={ctx.obj['host']}, port={ctx.obj['port']}")

            cli.add_command(test_host_port)
            result = cli_runner.invoke(cli, ["--host", "0.0.0.0", "--port", "9000", "test-host-port"])

        assert result.exit_code == 0
        assert "host=0.0.0.0" in result.output
        assert "port=9000" in result.output

    def test_cli_default_host_port(self, cli_runner: CliRunner) -> None:
        """Test default host and port values."""
        with patch("copaw.cli.main.read_last_api", return_value=None):
            # Create a context to check defaults
            @cli.command("test-defaults")
            @click.pass_context
            def test_defaults(ctx):
                click.echo(f"host={ctx.obj['host']}, port={ctx.obj['port']}")

            cli.add_command(test_defaults)
            result = cli_runner.invoke(cli, ["test-defaults"])

        assert "host=127.0.0.1" in result.output
        assert "port=8088" in result.output

    def test_cli_last_api_restore(self, cli_runner: CliRunner) -> None:
        """Test that last API host/port is restored."""
        with patch("copaw.cli.main.read_last_api", return_value=("192.168.1.1", 9000)):
            @cli.command("test-last-api")
            @click.pass_context
            def test_last_api(ctx):
                click.echo(f"host={ctx.obj['host']}, port={ctx.obj['port']}")

            cli.add_command(test_last_api)
            result = cli_runner.invoke(cli, ["test-last-api"])

        assert "host=192.168.1.1" in result.output
        assert "port=9000" in result.output


class TestCliCommands:
    """Tests for CLI commands registration."""

    def test_app_command_registered(self) -> None:
        """Test that app command is registered."""
        assert "app" in [cmd.name for cmd in cli.commands.values()]

    def test_channels_command_registered(self) -> None:
        """Test that channels command is registered."""
        assert "channels" in [cmd.name for cmd in cli.commands.values()]

    def test_chats_command_registered(self) -> None:
        """Test that chats command is registered."""
        assert "chats" in [cmd.name for cmd in cli.commands.values()]

    def test_clean_command_registered(self) -> None:
        """Test that clean command is registered."""
        assert "clean" in [cmd.name for cmd in cli.commands.values()]

    def test_cron_command_registered(self) -> None:
        """Test that cron command is registered."""
        assert "cron" in [cmd.name for cmd in cli.commands.values()]

    def test_env_command_registered(self) -> None:
        """Test that env command is registered."""
        assert "env" in [cmd.name for cmd in cli.commands.values()]

    def test_init_command_registered(self) -> None:
        """Test that init command is registered."""
        assert "init" in [cmd.name for cmd in cli.commands.values()]

    def test_models_command_registered(self) -> None:
        """Test that models command is registered."""
        assert "models" in [cmd.name for cmd in cli.commands.values()]

    def test_skills_command_registered(self) -> None:
        """Test that skills command is registered."""
        assert "skills" in [cmd.name for cmd in cli.commands.values()]

    def test_uninstall_command_registered(self) -> None:
        """Test that uninstall command is registered."""
        assert "uninstall" in [cmd.name for cmd in cli.commands.values()]
