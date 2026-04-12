# -*- coding: utf-8 -*-
"""Tests for tag_parser module."""
from __future__ import annotations

import pytest

from copaw.local_models.tag_parser import (
    ParsedToolCall,
    TextWithThinking,
    TextWithToolCalls,
    _generate_call_id,
    _parse_single_tool_call,
    extract_thinking_from_text,
    parse_tool_calls_from_text,
    text_contains_think_tag,
    text_contains_tool_call_tag,
)


class TestGenerateCallId:
    """Tests for _generate_call_id function."""

    def test_generate_call_id_format(self) -> None:
        """Test that generated ID has correct format."""
        call_id = _generate_call_id()
        assert call_id.startswith("call_")
        assert len(call_id) == 17  # "call_" + 12 hex chars

    def test_generate_call_id_uniqueness(self) -> None:
        """Test that generated IDs are unique."""
        ids = [_generate_call_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestParseSingleToolCall:
    """Tests for _parse_single_tool_call function."""

    def test_parse_valid_tool_call(self) -> None:
        """Test parsing a valid tool call JSON."""
        raw_text = '{"name": "get_weather", "arguments": {"location": "Beijing"}}'
        result = _parse_single_tool_call(raw_text)

        assert result is not None
        assert result.name == "get_weather"
        assert result.arguments == {"location": "Beijing"}

    def test_parse_tool_call_with_string_arguments(self) -> None:
        """Test parsing tool call with arguments as JSON string."""
        raw_text = '{"name": "test", "arguments": "{\\"key\\": \\"value\\"}"}'
        result = _parse_single_tool_call(raw_text)

        assert result is not None
        assert result.name == "test"
        assert result.arguments == {"key": "value"}

    def test_parse_invalid_json(self) -> None:
        """Test parsing invalid JSON returns None."""
        raw_text = "not valid json"
        result = _parse_single_tool_call(raw_text)

        assert result is None

    def test_parse_missing_name_field(self) -> None:
        """Test parsing JSON without name field returns None."""
        raw_text = '{"arguments": {"key": "value"}}'
        result = _parse_single_tool_call(raw_text)

        assert result is None

    def test_parse_empty_name(self) -> None:
        """Test parsing JSON with empty name returns None."""
        raw_text = '{"name": "", "arguments": {}}'
        result = _parse_single_tool_call(raw_text)

        assert result is None

    def test_parse_missing_arguments(self) -> None:
        """Test parsing JSON without arguments defaults to empty dict."""
        raw_text = '{"name": "test_func"}'
        result = _parse_single_tool_call(raw_text)

        assert result is not None
        assert result.name == "test_func"
        assert result.arguments == {}


class TestTextContainsThinkTag:
    """Tests for text_contains_think_tag function."""

    def test_contains_think_tag_true(self) -> None:
        """Test detection of think tag."""
        text = "Some text \u003cthink\u003ewith thinking\u003c/think\u003e"
        assert text_contains_think_tag(text) is True

    def test_contains_think_tag_false(self) -> None:
        """Test detection when no think tag present."""
        text = "Some regular text without tags"
        assert text_contains_think_tag(text) is False

    def test_contains_think_tag_partial(self) -> None:
        """Test detection of partial think tag (opening only)."""
        text = "Some text \u003cthink\u003estill thinking"
        assert text_contains_think_tag(text) is True


class TestExtractThinkingFromText:
    """Tests for extract_thinking_from_text function."""

    def test_extract_complete_thinking(self) -> None:
        """Test extracting a complete thinking block."""
        think_start = "\u003cthink\u003e"
        think_end = "\u003c/think\u003e"
        text = f"Before. {think_start}Thinking content{think_end} After."
        result = extract_thinking_from_text(text)

        assert result.thinking == "Thinking content"
        assert "Before" in result.remaining_text
        assert "After" in result.remaining_text
        assert result.has_open_tag is False

    def test_extract_no_thinking(self) -> None:
        """Test extracting from text without thinking tags."""
        text = "Just regular text without any thinking tags."
        result = extract_thinking_from_text(text)

        assert result.thinking == ""
        assert result.remaining_text == text
        assert result.has_open_tag is False

    def test_extract_unclosed_thinking(self) -> None:
        """Test extracting from text with unclosed thinking tag."""
        think_start = "\u003cthink\u003e"
        text = f"Before. {think_start}Still thinking..."
        result = extract_thinking_from_text(text)

        assert result.has_open_tag is True
        assert "Still thinking" in result.thinking
        assert "Before" in result.remaining_text

    def test_extract_multiline_thinking(self) -> None:
        """Test extracting multiline thinking content."""
        think_start = "\u003cthink\u003e"
        think_end = "\u003c/think\u003e"
        text = f"""{think_start}
Line 1
Line 2
Line 3
{think_end}
Result text."""
        result = extract_thinking_from_text(text)

        assert "Line 1" in result.thinking
        assert "Line 2" in result.thinking
        assert "Line 3" in result.thinking
        assert "Result text" in result.remaining_text


class TestTextContainsToolCallTag:
    """Tests for text_contains_tool_call_tag function."""

    def test_contains_tool_call_tag_true(self) -> None:
        """Test detection of tool call tag."""
        text = "Some text \u003ctool_call\u003ewith tool call\u003c/tool_call\u003e"
        assert text_contains_tool_call_tag(text) is True

    def test_contains_tool_call_tag_false(self) -> None:
        """Test detection when no tool call tag present."""
        text = "Some regular text without tags"
        assert text_contains_tool_call_tag(text) is False

    def test_contains_tool_call_tag_partial(self) -> None:
        """Test detection of partial tool call tag."""
        text = "Some text \u003ctool_call\u003estill calling"
        assert text_contains_tool_call_tag(text) is True


class TestParseToolCallsFromText:
    """Tests for parse_tool_calls_from_text function."""

    def test_parse_single_tool_call(self) -> None:
        """Test parsing a single tool call."""
        tool_start = "\u003ctool_call\u003e"
        tool_end = "\u003c/tool_call\u003e"
        text = f"""Before text.
{tool_start}
{{"name": "get_weather", "arguments": {{"location": "Beijing"}}}}
{tool_end}
After text."""
        result = parse_tool_calls_from_text(text)

        assert result.text_before == "Before text."
        assert result.text_after == "After text."
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == {"location": "Beijing"}
        assert result.has_open_tag is False

    def test_parse_multiple_tool_calls(self) -> None:
        """Test parsing multiple tool calls."""
        tool_start = "\u003ctool_call\u003e"
        tool_end = "\u003c/tool_call\u003e"
        text = f"""Start.
{tool_start}
{{"name": "func1", "arguments": {{"a": 1}}}}
{tool_end}
Middle.
{tool_start}
{{"name": "func2", "arguments": {{"b": 2}}}}
{tool_end}
End."""
        result = parse_tool_calls_from_text(text)

        assert len(result.tool_calls) == 2
        assert result.tool_calls[0].name == "func1"
        assert result.tool_calls[1].name == "func2"

    def test_parse_no_tool_calls(self) -> None:
        """Test parsing text without tool calls."""
        text = "Just regular text without any tool calls."
        result = parse_tool_calls_from_text(text)

        assert len(result.tool_calls) == 0
        assert result.text_before == text
        assert result.has_open_tag is False

    def test_parse_unclosed_tool_call(self) -> None:
        """Test parsing text with unclosed tool call tag."""
        tool_start = "\u003ctool_call\u003e"
        text = f"Before. {tool_start}{{\"name\": \"test\""
        result = parse_tool_calls_from_text(text)

        assert result.has_open_tag is True
        assert result.text_before == "Before."
        assert len(result.tool_calls) == 0

    def test_parse_invalid_tool_call_json(self) -> None:
        """Test that invalid JSON in tool call is skipped."""
        tool_start = "\u003ctool_call\u003e"
        tool_end = "\u003c/tool_call\u003e"
        text = f"""{tool_start}
not valid json
{tool_end}
{tool_start}
{{"name": "valid_func", "arguments": {{}}}}
{tool_end}"""
        result = parse_tool_calls_from_text(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "valid_func"

    def test_parse_tool_call_after_complete(self) -> None:
        """Test unclosed tool call after complete ones."""
        tool_start = "\u003ctool_call\u003e"
        tool_end = "\u003c/tool_call\u003e"
        text = f"""{tool_start}
{{"name": "complete", "arguments": {{}}}}
{tool_end}
Some text.
{tool_start}
incomplete tool call"""
        result = parse_tool_calls_from_text(text)

        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "complete"
        assert result.has_open_tag is True


class TestTextWithThinking:
    """Tests for TextWithThinking dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        result = TextWithThinking()
        assert result.thinking == ""
        assert result.remaining_text == ""
        assert result.has_open_tag is False


class TestTextWithToolCalls:
    """Tests for TextWithToolCalls dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        result = TextWithToolCalls()
        assert result.text_before == ""
        assert result.text_after == ""
        assert result.tool_calls == []
        assert result.has_open_tag is False
        assert result.partial_tool_text == ""


class TestParsedToolCall:
    """Tests for ParsedToolCall dataclass."""

    def test_parsed_tool_call(self) -> None:
        """Test creating a ParsedToolCall."""
        call = ParsedToolCall(
            id="call_123",
            name="test_func",
            arguments={"key": "value"},
            raw_arguments='{"key": "value"}',
        )

        assert call.id == "call_123"
        assert call.name == "test_func"
        assert call.arguments == {"key": "value"}
        assert call.raw_arguments == '{"key": "value"}'
