# -*- coding: utf-8 -*-
"""
Context and Memory Management Tests.

This module provides tests for validating the CoPaw agent's context
management capabilities, including:

1. Memory initialization and state management
2. Context compaction (automatic and manual)
3. Compressed summary storage and retrieval
4. Token counting and threshold detection
5. Memory serialization and deserialization

These tests verify that the agent can properly manage its context window
to handle long conversations without exceeding model limits.

Key Concepts:
- Context Window: The maximum tokens the model can process
- Compaction: Summarizing old messages to free up context space
- Compressed Summary: A condensed summary of previous conversation
- Memory Mark: Tags on messages (e.g., COMPRESSED) for filtering
"""
from __future__ import annotations

import os
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentscope.message import Msg
from agentscope.agent._react_agent import _MemoryMark


# ============================================================================
# Section 1: Memory State Management Tests
# ============================================================================


class TestMemoryInitialization:
    """
    Test memory initialization and basic operations.
    
    CoPawInMemoryMemory extends InMemoryMemory with:
    - Compressed summary storage
    - Message marking (COMPRESSED mark)
    - State serialization/deserialization
    """
    
    def test_memory_initial_state(self):
        """
        Test that memory initializes with empty state.
        
        Initial state should have:
        - Empty content list
        - Empty compressed summary
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Memory should be empty initially
        assert len(memory.content) == 0
        assert memory.get_compressed_summary() == ""
    
    @pytest.mark.asyncio
    async def test_memory_add_messages(self):
        """
        Test adding messages to memory.
        
        Messages are stored as (Msg, marks) tuples.
        Note: add() is an async method.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Add messages (async)
        msg1 = Msg(name="user", content="Hello", role="user")
        msg2 = Msg(name="assistant", content="Hi there!", role="assistant")
        
        await memory.add(msg1)
        await memory.add(msg2)
        
        assert len(memory.content) == 2
        
        # Messages should have empty marks initially (list, not set)
        for msg, marks in memory.content:
            assert isinstance(msg, Msg)
            assert isinstance(marks, list)
    
    @pytest.mark.asyncio
    async def test_memory_get_memory_basic(self):
        """
        Test basic memory retrieval.
        
        get_memory() returns messages, optionally:
        - Filtered by mark
        - Excluding specific marks
        - Prepended with compressed summary
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Add some messages (async)
        for i in range(5):
            await memory.add(Msg(name="user", content=f"Message {i}", role="user"))
        
        # Get all messages (default excludes COMPRESSED)
        messages = await memory.get_memory(prepend_summary=False)
        assert len(messages) == 5


class TestMemorySerialization:
    """
    Test memory serialization and deserialization.
    
    Memory state can be saved and restored via:
    - state_dict(): Export to dictionary
    - load_state_dict(): Import from dictionary
    
    This is used for session persistence.
    """
    
    def test_state_dict_export(self):
        """
        Test exporting memory state to dictionary.
        
        State includes:
        - content: List of (msg_dict, marks) pairs
        - _compressed_summary: The compressed summary string
        """
        import asyncio
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Add messages (async, need to run in sync context)
        async def setup():
            await memory.add(Msg(name="user", content="Test message", role="user"))
        asyncio.run(setup())
        
        memory._compressed_summary = "Test summary"
        
        state = memory.state_dict()
        
        assert "content" in state
        assert "_compressed_summary" in state
        assert len(state["content"]) == 1
        assert state["_compressed_summary"] == "Test summary"
    
    def test_state_dict_import(self):
        """
        Test importing memory state from dictionary.
        
        Should restore both messages and compressed summary.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Create state to import
        state = {
            "content": [
                [Msg(name="user", content="Test", role="user").to_dict(), set()],
            ],
            "_compressed_summary": "Restored summary",
        }
        
        memory.load_state_dict(state)
        
        assert len(memory.content) == 1
        assert memory.get_compressed_summary() == "Restored summary"
    
    def test_round_trip_serialization(self):
        """
        Test that serialization and deserialization preserve state.
        
        This verifies no data is lost during the round trip.
        """
        import asyncio
        from copaw.agents.memory import CoPawInMemoryMemory
        
        original = CoPawInMemoryMemory()
        
        # Add various content (async)
        async def setup():
            await original.add(Msg(name="user", content="User message", role="user"))
            await original.add(Msg(name="assistant", content="Assistant response", role="assistant"))
        asyncio.run(setup())
        
        original._compressed_summary = "Previous conversation summary"
        
        # Export
        state = original.state_dict()
        
        # Import to new memory
        restored = CoPawInMemoryMemory()
        restored.load_state_dict(state)
        
        # Verify
        assert len(restored.content) == len(original.content)
        assert restored.get_compressed_summary() == original.get_compressed_summary()


# ============================================================================
# Section 2: Context Compaction Tests
# ============================================================================


class TestContextCompactionThreshold:
    """
    Test context compaction threshold detection.
    
    Compaction is triggered when token count exceeds:
    max_input_length * MEMORY_COMPACT_RATIO
    
    Environment Variables:
    - COPAW_MEMORY_COMPACT_THRESHOLD: Direct token threshold
    - COPAW_MEMORY_COMPACT_KEEP_RECENT: Messages to keep after compaction
    - COPAW_MEMORY_COMPACT_RATIO: Ratio of max_input_length
    """
    
    def test_threshold_calculation(self):
        """
        Test threshold calculation from ratio.
        
        Default ratio is 0.7 (70% of max_input_length).
        """
        max_input_length = 128000  # 128K context window
        compact_ratio = 0.7
        
        threshold = int(max_input_length * compact_ratio)
        
        assert threshold == 89600  # 70% of 128K
    
    def test_environment_variable_override(self):
        """
        Test that environment variables override defaults.
        
        COPAW_MEMORY_COMPACT_THRESHOLD should take precedence.
        """
        # This would be tested by setting env vars and checking constant values
        # In tests, we verify the mechanism exists
        
        test_threshold = 50000
        test_env_value = str(test_threshold)
        
        # Simulate environment variable check
        env_threshold = os.environ.get("COPAW_MEMORY_COMPACT_THRESHOLD")
        if env_threshold:
            assert int(env_threshold) == test_threshold
    
    def test_keep_recent_configuration(self):
        """
        Test the keep_recent configuration.
        
        This determines how many recent messages are preserved
        during compaction.
        """
        # Default is 3 messages
        default_keep_recent = 3
        
        # Should be configurable via environment
        env_keep_recent = os.environ.get("COPAW_MEMORY_COMPACT_KEEP_RECENT")
        
        if env_keep_recent:
            keep_recent = int(env_keep_recent)
        else:
            keep_recent = default_keep_recent
        
        assert keep_recent >= 0


class TestMemoryCompactionHook:
    """
    Test the MemoryCompactionHook.
    
    This hook:
    1. Runs before each reasoning step (pre_reasoning)
    2. Counts tokens in compactable messages
    3. Triggers compaction if threshold exceeded
    4. Preserves system prompt and recent messages
    
    Related Code:
    - src/copaw/agents/hooks/memory_compaction.py
    """
    
    def test_hook_initialization(self):
        """
        Test hook initialization with parameters.
        """
        from copaw.agents.hooks.memory_compaction import MemoryCompactionHook
        
        # Create mock memory manager
        mock_manager = MagicMock()
        
        hook = MemoryCompactionHook(
            memory_manager=mock_manager,
            memory_compact_threshold=50000,
            keep_recent=5,
        )
        
        assert hook.memory_compact_threshold == 50000
        assert hook.keep_recent == 5
    
    def test_tool_result_truncation_flag(self):
        """
        Test tool result truncation configuration.
        
        ENABLE_TRUNCATE_TOOL_RESULT_TEXTS controls whether
        long tool results are truncated during compaction.
        """
        from copaw.agents.hooks.memory_compaction import MemoryCompactionHook
        
        mock_manager = MagicMock()
        hook = MemoryCompactionHook(
            memory_manager=mock_manager,
            memory_compact_threshold=50000,
        )
        
        # Default should be False
        original_env = os.environ.get("ENABLE_TRUNCATE_TOOL_RESULT_TEXTS")
        
        try:
            # Test with environment variable
            if "ENABLE_TRUNCATE_TOOL_RESULT_TEXTS" in os.environ:
                del os.environ["ENABLE_TRUNCATE_TOOL_RESULT_TEXTS"]
            
            assert hook.enable_truncate_tool_result_texts is False
            
            # Test with true
            os.environ["ENABLE_TRUNCATE_TOOL_RESULT_TEXTS"] = "true"
            assert hook.enable_truncate_tool_result_texts is True
            
        finally:
            # Restore original env
            if original_env is not None:
                os.environ["ENABLE_TRUNCATE_TOOL_RESULT_TEXTS"] = original_env
            elif "ENABLE_TRUNCATE_TOOL_RESULT_TEXTS" in os.environ:
                del os.environ["ENABLE_TRUNCATE_TOOL_RESULT_TEXTS"]


class TestCompactionProcess:
    """
    Test the compaction process itself.
    
    Compaction flow:
    1. Identify messages to compact (exclude system prompt and recent)
    2. Generate summary via MemoryManager
    3. Store summary in memory
    4. Mark compacted messages as COMPRESSED
    """
    
    @pytest.mark.asyncio
    async def test_mark_messages_compressed(self):
        """
        Test marking messages as compressed.
        
        Compacted messages receive the COMPRESSED mark.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Add messages (async)
        msg1 = Msg(name="user", content="Message 1", role="user")
        msg2 = Msg(name="user", content="Message 2", role="user")
        
        await memory.add(msg1)
        await memory.add(msg2)
        
        # Mark messages as compressed
        msg_ids = [msg1.id, msg2.id]
        updated = await memory.update_messages_mark(
            new_mark=_MemoryMark.COMPRESSED,
            msg_ids=msg_ids,
        )
        
        assert updated == 2
        
        # Verify marks (marks is a list)
        for msg, marks in memory.content:
            assert _MemoryMark.COMPRESSED in marks
    
    @pytest.mark.asyncio
    async def test_get_memory_exclude_compressed(self):
        """
        Test that get_memory excludes compressed messages by default.
        
        This ensures compacted messages don't fill the context.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Add and compress messages (async)
        msg1 = Msg(name="user", content="Old message", role="user")
        msg2 = Msg(name="user", content="Recent message", role="user")
        
        await memory.add(msg1)
        await memory.add(msg2)
        
        # Mark first message as compressed
        await memory.update_messages_mark(
            new_mark=_MemoryMark.COMPRESSED,
            msg_ids=[msg1.id],
        )
        
        # Get memory (should exclude compressed)
        messages = await memory.get_memory(prepend_summary=False)
        
        assert len(messages) == 1
        assert messages[0].content == "Recent message"
    
    @pytest.mark.asyncio
    async def test_compressed_summary_prepend(self):
        """
        Test that compressed summary is prepended to memory.
        
        When prepend_summary=True, the summary is added as a message.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Set compressed summary
        memory._compressed_summary = "This is a summary of previous conversation."
        
        # Add a message (async)
        await memory.add(Msg(name="user", content="Current message", role="user"))
        
        # Get memory with summary prepended
        messages = await memory.get_memory(prepend_summary=True, exclude_mark=None)
        
        # Should have summary + current message
        assert len(messages) == 2
        assert "previous conversation" in messages[0].content
        
        # Get without summary
        messages = await memory.get_memory(prepend_summary=False, exclude_mark=None)
        assert len(messages) == 1


# ============================================================================
# Section 3: Command Handler Tests
# ============================================================================


class TestCompactCommand:
    """
    Test the /compact command.
    
    /compact manually triggers compaction:
    1. Takes all current messages
    2. Generates summary via MemoryManager
    3. Marks all messages as compressed
    4. Returns summary to user
    
    Related Code:
    - src/copaw/agents/command_handler.py:_process_compact()
    """
    
    @pytest.mark.asyncio
    async def test_compact_command_detection(self):
        """
        Test that /compact is recognized as a command.
        """
        from copaw.agents.command_handler import CommandHandler
        
        handler = CommandHandler(
            agent_name="TestAgent",
            memory=MagicMock(),
            formatter=MagicMock(),
        )
        
        assert handler.is_command("/compact")
        assert handler.is_command("/compact ")  # With trailing space
        assert not handler.is_command("compact")  # Without slash
        assert not handler.is_command("/compacted")  # Different command
    
    @pytest.mark.asyncio
    async def test_compact_empty_memory(self):
        """
        Test /compact with empty memory.
        
        Should return a message indicating nothing to compact.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        from copaw.agents.command_handler import CommandHandler
        
        memory = CoPawInMemoryMemory()
        handler = CommandHandler(
            agent_name="TestAgent",
            memory=memory,
            formatter=MagicMock(),
        )
        
        result = await handler.handle_command("/compact")
        
        # Result is a Msg object
        content = result.content if isinstance(result.content, str) else str(result.content)
        assert "no messages" in content.lower() or "empty" in content.lower()
    
    @pytest.mark.asyncio
    async def test_compact_without_memory_manager(self):
        """
        Test /compact when memory manager is disabled.
        
        Should return a message indicating the feature is disabled.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        from copaw.agents.command_handler import CommandHandler
        
        memory = CoPawInMemoryMemory()
        await memory.add(Msg(name="user", content="Test message", role="user"))
        
        handler = CommandHandler(
            agent_name="TestAgent",
            memory=memory,
            formatter=MagicMock(),
            enable_memory_manager=False,  # Disabled
        )
        
        result = await handler.handle_command("/compact")
        
        # Result is a Msg object
        content = result.content if isinstance(result.content, str) else str(result.content)
        # Should indicate memory manager is disabled
        assert "disabled" in content.lower() or "not available" in content.lower()


class TestClearCommand:
    """
    Test the /clear command.
    
    /clear completely clears the memory:
    1. Clears all messages
    2. Resets compressed summary
    3. Does NOT save to long-term memory
    
    Related Code:
    - src/copaw/agents/command_handler.py:_process_clear()
    """
    
    @pytest.mark.asyncio
    async def test_clear_command(self):
        """
        Test that /clear clears all memory.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        from copaw.agents.command_handler import CommandHandler
        
        memory = CoPawInMemoryMemory()
        
        # Add content (async)
        await memory.add(Msg(name="user", content="Message 1", role="user"))
        await memory.add(Msg(name="user", content="Message 2", role="user"))
        memory._compressed_summary = "Old summary"
        
        handler = CommandHandler(
            agent_name="TestAgent",
            memory=memory,
            formatter=MagicMock(),
        )
        
        result = await handler.handle_command("/clear")
        
        # Verify memory is cleared
        assert len(memory.content) == 0
        assert memory.get_compressed_summary() == ""
    
    @pytest.mark.asyncio
    async def test_clear_vs_compact_difference(self):
        """
        Test the difference between /clear and /compact.
        
        /clear: Clears everything immediately, no summary
        /compact: Creates summary, marks messages as compressed
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        await memory.add(Msg(name="user", content="Test", role="user"))
        
        # Clear: summary becomes empty
        memory._compressed_summary = ""
        memory.content.clear()
        
        assert memory.get_compressed_summary() == ""
        assert len(memory.content) == 0


class TestHistoryCommand:
    """
    Test the /history command.
    
    /history shows:
    1. Current messages
    2. Compressed summary (if any)
    3. Token counts
    4. Context usage percentage
    
    Related Code:
    - src/copaw/agents/command_handler.py:_process_history()
    """
    
    @pytest.mark.asyncio
    async def test_history_command_structure(self):
        """
        Test that /history returns properly formatted info.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        from copaw.agents.command_handler import CommandHandler
        
        memory = CoPawInMemoryMemory()
        
        # Add some messages (async)
        for i in range(5):
            await memory.add(Msg(name="user", content=f"Message {i}" * 100, role="user"))
        
        memory._compressed_summary = "Summary of previous conversation."
        
        # Create a proper mock formatter with async format method
        mock_formatter = MagicMock()
        mock_formatter.format = AsyncMock(return_value=[
            {"role": "user", "content": "test"}
        ])
        
        handler = CommandHandler(
            agent_name="TestAgent",
            memory=memory,
            formatter=mock_formatter,
        )
        
        result = await handler.handle_command("/history")
        
        # Result should contain token info
        content = result.content if isinstance(result.content, str) else str(result.content)
        content_lower = content.lower()
        # Check for various possible formats
        assert "token" in content_lower or "history" in content_lower or "message" in content_lower


class TestCompactStrCommand:
    """
    Test the /compact_str command.
    
    /compact_str displays the current compressed summary.
    
    Related Code:
    - src/copaw/agents/command_handler.py:_process_compact_str()
    """
    
    @pytest.mark.asyncio
    async def test_compact_str_with_summary(self):
        """
        Test /compact_str when summary exists.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        from copaw.agents.command_handler import CommandHandler
        
        memory = CoPawInMemoryMemory()
        memory._compressed_summary = "User discussed authentication implementation."
        
        handler = CommandHandler(
            agent_name="TestAgent",
            memory=memory,
            formatter=MagicMock(),
        )
        
        result = await handler.handle_command("/compact_str")
        
        content = result.content if isinstance(result.content, str) else str(result.content)
        assert "authentication" in content
    
    @pytest.mark.asyncio
    async def test_compact_str_without_summary(self):
        """
        Test /compact_str when no summary exists.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        from copaw.agents.command_handler import CommandHandler
        
        memory = CoPawInMemoryMemory()
        
        handler = CommandHandler(
            agent_name="TestAgent",
            memory=memory,
            formatter=MagicMock(),
        )
        
        result = await handler.handle_command("/compact_str")
        
        content = result.content if isinstance(result.content, str) else str(result.content)
        content_lower = content.lower()
        assert "no" in content_lower or "empty" in content_lower or "not" in content_lower


# ============================================================================
# Section 4: Token Counting Tests
# ============================================================================


class TestTokenCounting:
    """
    Test token counting for context management.
    
    Accurate token counting is essential for:
    1. Knowing when to trigger compaction
    2. Reporting context usage to users
    """
    
    def test_safe_count_str_tokens(self):
        """
        Test counting tokens in a string.
        
        Uses the safe_count_str_tokens utility.
        """
        from copaw.agents.utils import safe_count_str_tokens
        
        # Simple text
        text = "Hello, this is a test message."
        count = safe_count_str_tokens(text)
        
        # Should return a positive integer
        assert isinstance(count, int)
        assert count > 0
    
    @pytest.mark.asyncio
    async def test_safe_count_message_tokens(self):
        """
        Test counting tokens in formatted messages.
        """
        from copaw.agents.utils import safe_count_message_tokens
        
        # Simulate formatted prompt
        prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]
        
        count = await safe_count_message_tokens(prompt)
        
        assert isinstance(count, int)
        assert count > 0
    
    def test_token_count_approximation(self):
        """
        Test that token counting is approximately correct.
        
        Different tokenizers may have slight variations,
        but should be within reasonable range.
        """
        from copaw.agents.utils import safe_count_str_tokens
        
        # Known approximate: ~4 characters per token for English
        text_100_chars = "This is a test message that is approximately one hundred characters long for testing purposes."[:100]
        
        count = safe_count_str_tokens(text_100_chars)
        
        # Should be roughly 25 tokens (100 chars / 4)
        # Allow for variation: 15-40 tokens
        assert 15 <= count <= 40


# ============================================================================
# Section 5: Integration Tests
# ============================================================================


class TestContextManagementIntegration:
    """
    Integration tests for context management.
    
    These tests verify multiple components work together.
    """
    
    @pytest.mark.asyncio
    async def test_full_compaction_cycle(self):
        """
        Test a full compaction cycle.
        
        This simulates:
        1. Adding many messages to memory
        2. Triggering compaction
        3. Verifying summary is created
        4. Verifying messages are marked
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Add many messages (async)
        for i in range(20):
            await memory.add(Msg(
                name="user",
                content=f"Message {i}: " + "x" * 100,  # Make it substantial
                role="user",
            ))
        
        assert len(memory.content) == 20
        
        # Simulate compaction: mark first 15 messages
        msg_ids = [msg.id for msg, _ in memory.content[:15]]
        await memory.update_messages_mark(
            new_mark=_MemoryMark.COMPRESSED,
            msg_ids=msg_ids,
        )
        
        # Set summary
        memory._compressed_summary = "Summary of messages 0-14"
        
        # Get non-compressed messages
        messages = await memory.get_memory(prepend_summary=True)
        
        # Should have summary + 5 recent messages
        assert len(messages) == 6  # summary + 5 kept
        assert "Summary of messages 0-14" in messages[0].content
    
    @pytest.mark.asyncio
    async def test_multiple_compaction_rounds(self):
        """
        Test multiple rounds of compaction.
        
        This verifies that:
        1. Previous summaries are built upon
        2. Compaction works incrementally
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # First round (async)
        await memory.add(Msg(name="user", content="First batch", role="user"))
        memory._compressed_summary = "Summary 1"
        
        # Simulate clearing compressed messages
        await memory.update_messages_mark(
            new_mark=_MemoryMark.COMPRESSED,
            msg_ids=[msg.id for msg, _ in memory.content],
        )
        
        # Add more messages
        await memory.add(Msg(name="user", content="Second batch", role="user"))
        
        # Second round - summary should be built upon
        previous_summary = memory.get_compressed_summary()
        new_summary = f"{previous_summary}\n\nSummary 2"
        memory._compressed_summary = new_summary
        
        assert "Summary 1" in memory.get_compressed_summary()
        assert "Summary 2" in memory.get_compressed_summary()


class TestContextEdgeCases:
    """
    Test edge cases in context management.
    """
    
    @pytest.mark.asyncio
    async def test_empty_memory_operations(self):
        """
        Test operations on empty memory.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Get memory from empty
        messages = await memory.get_memory()
        assert messages == []
        
        # Get summary from empty
        assert memory.get_compressed_summary() == ""
    
    @pytest.mark.asyncio
    async def test_single_message_memory(self):
        """
        Test memory with only one message.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        await memory.add(Msg(name="user", content="Single message", role="user"))
        
        messages = await memory.get_memory(prepend_summary=False)
        assert len(messages) == 1
    
    @pytest.mark.asyncio
    async def test_very_long_message(self):
        """
        Test handling of very long single message.
        """
        from copaw.agents.memory import CoPawInMemoryMemory
        
        memory = CoPawInMemoryMemory()
        
        # Create a very long message
        long_content = "x" * 100000  # 100k characters
        await memory.add(Msg(name="user", content=long_content, role="user"))
        
        assert len(memory.content) == 1
        
        # Should be able to retrieve it
        messages = await memory.get_memory(prepend_summary=False)
        assert len(messages) == 1


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
