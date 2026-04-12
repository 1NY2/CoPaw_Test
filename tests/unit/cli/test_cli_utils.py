# -*- coding: utf-8 -*-
"""Tests for CLI utils module."""
from __future__ import annotations

from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from copaw.cli.utils import (
    prompt_confirm,
    prompt_path,
    prompt_choice,
    prompt_select,
    prompt_checkbox,
)


class TestPromptConfirm:
    """Tests for prompt_confirm function."""

    def test_prompt_confirm_yes(self) -> None:
        """Test confirm prompt with Yes selection."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = True

            result = prompt_confirm("Continue?", default=False)

            assert result is True
            mock_select.assert_called_once()

    def test_prompt_confirm_no(self) -> None:
        """Test confirm prompt with No selection."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = False

            result = prompt_confirm("Continue?", default=True)

            assert result is False

    def test_prompt_confirm_ctrl_c_default_false(self) -> None:
        """Test confirm prompt returns default on Ctrl+C."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = None

            result = prompt_confirm("Continue?", default=False)

            assert result is False

    def test_prompt_confirm_ctrl_c_default_true(self) -> None:
        """Test confirm prompt returns default True on Ctrl+C."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = None

            result = prompt_confirm("Continue?", default=True)

            assert result is True


class TestPromptPath:
    """Tests for prompt_path function."""

    def test_prompt_path_exists(self, tmp_path: Path) -> None:
        """Test path prompt with existing path."""
        existing_file = tmp_path / "test.txt"
        existing_file.write_text("test")

        with patch("click.prompt") as mock_prompt:
            mock_prompt.return_value = str(existing_file)

            result = prompt_path("Enter path:")

            assert result == str(existing_file.resolve())

    def test_prompt_path_not_exists_continue(self, tmp_path: Path) -> None:
        """Test path prompt with non-existing path, continue anyway."""
        nonexistent = tmp_path / "nonexistent.txt"

        with patch("click.prompt") as mock_prompt:
            mock_prompt.return_value = str(nonexistent)
            with patch("copaw.cli.utils.prompt_confirm", return_value=True):
                result = prompt_path("Enter path:")

        assert result == str(nonexistent)

    def test_prompt_path_not_exists_retry(self, tmp_path: Path) -> None:
        """Test path prompt with non-existing path, retry."""
        nonexistent = tmp_path / "nonexistent.txt"
        existing = tmp_path / "existing.txt"
        existing.write_text("test")

        with patch("click.prompt") as mock_prompt:
            # First call: nonexistent, second call: existing
            mock_prompt.side_effect = [str(nonexistent), str(existing)]
            with patch("copaw.cli.utils.prompt_confirm", return_value=False):
                result = prompt_path("Enter path:")

        assert result == str(existing.resolve())

    def test_prompt_path_empty(self) -> None:
        """Test path prompt with empty input."""
        with patch("click.prompt") as mock_prompt:
            mock_prompt.return_value = ""

            result = prompt_path("Enter path:")

            assert result == ""


class TestPromptChoice:
    """Tests for prompt_choice function."""

    def test_prompt_choice_selection(self) -> None:
        """Test choice prompt with selection."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "option2"

            result = prompt_choice("Pick one:", ["option1", "option2", "option3"])

            assert result == "option2"

    def test_prompt_choice_ctrl_c_returns_default(self) -> None:
        """Test choice prompt returns default on Ctrl+C."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = None

            result = prompt_choice(
                "Pick one:",
                ["option1", "option2"],
                default="option2",
            )

            assert result == "option2"

    def test_prompt_choice_ctrl_c_returns_first(self) -> None:
        """Test choice prompt returns first option on Ctrl+C without default."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = None

            result = prompt_choice("Pick one:", ["option1", "option2"])

            assert result == "option1"


class TestPromptSelect:
    """Tests for prompt_select function."""

    def test_prompt_select_selection(self) -> None:
        """Test select prompt with selection."""
        options = [
            ("Option 1", "value1"),
            ("Option 2", "value2"),
            ("Option 3", "value3"),
        ]

        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "value2"

            result = prompt_select("Pick one:", options)

            assert result == "value2"

    def test_prompt_select_ctrl_c(self) -> None:
        """Test select prompt returns None on Ctrl+C."""
        options = [
            ("Option 1", "value1"),
            ("Option 2", "value2"),
        ]

        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = None

            result = prompt_select("Pick one:", options)

            assert result is None

    def test_prompt_select_with_default(self) -> None:
        """Test select prompt with default preselection."""
        options = [
            ("Option 1", "value1"),
            ("Option 2", "value2"),
        ]

        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "value2"

            result = prompt_select("Pick one:", options, default="value2")

            assert result == "value2"


class TestPromptCheckbox:
    """Tests for prompt_checkbox function."""

    def test_prompt_checkbox_selection(self) -> None:
        """Test checkbox prompt with selections."""
        options = [
            ("Item 1", "value1"),
            ("Item 2", "value2"),
            ("Item 3", "value3"),
        ]

        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = ["value1", "value3"]

            result = prompt_checkbox("Select items:", options)

            assert result == ["value1", "value3"]

    def test_prompt_checkbox_ctrl_c(self) -> None:
        """Test checkbox prompt returns None on Ctrl+C."""
        options = [
            ("Item 1", "value1"),
            ("Item 2", "value2"),
        ]

        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = None

            result = prompt_checkbox("Select items:", options)

            assert result is None

    def test_prompt_checkbox_with_checked(self) -> None:
        """Test checkbox prompt with pre-checked items."""
        options = [
            ("Item 1", "value1"),
            ("Item 2", "value2"),
            ("Item 3", "value3"),
        ]

        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = ["value1", "value2"]

            result = prompt_checkbox(
                "Select items:",
                options,
                checked={"value1", "value2"},
            )

            assert "value1" in result
            assert "value2" in result

    def test_prompt_checkbox_select_all(self) -> None:
        """Test checkbox prompt select all toggle."""
        options = [
            ("Item 1", "value1"),
            ("Item 2", "value2"),
        ]

        with patch("questionary.checkbox") as mock_checkbox:
            # First call: select all toggle, second call: normal selection
            mock_checkbox.return_value.ask.side_effect = [
                ["__select_all__"],  # Select all toggle
                ["value1", "value2"],  # All items selected
            ]

            result = prompt_checkbox("Select items:", options)

            assert set(result) == {"value1", "value2"}

    def test_prompt_checkbox_deselect_all(self) -> None:
        """Test checkbox prompt deselect all toggle."""
        options = [
            ("Item 1", "value1"),
            ("Item 2", "value2"),
        ]

        with patch("questionary.checkbox") as mock_checkbox:
            # First call: deselect all toggle (all already checked), second call: empty selection
            mock_checkbox.return_value.ask.side_effect = [
                ["__select_all__"],  # Deselect all toggle
                [],  # Nothing selected
            ]

            result = prompt_checkbox(
                "Select items:",
                options,
                checked={"value1", "value2"},
            )

            assert result == []

    def test_prompt_checkbox_without_select_all(self) -> None:
        """Test checkbox prompt without select all option."""
        options = [
            ("Item 1", "value1"),
            ("Item 2", "value2"),
        ]

        with patch("questionary.checkbox") as mock_checkbox:
            mock_checkbox.return_value.ask.return_value = ["value1"]

            result = prompt_checkbox(
                "Select items:",
                options,
                select_all_option=False,
            )

            assert result == ["value1"]
