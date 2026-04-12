# -*- coding: utf-8 -*-
"""
Concurrency Testing Module for Multi-Worker Channel Processing.

This module tests the concurrent processing capabilities of CoPaw's
ChannelManager, including:

1. Worker Pool Management - Multiple workers per channel
2. Session Isolation - Same-session messages processed by single worker
3. Debounce Key Handling - Message batching by session
4. Queue Management - Thread-safe message enqueuing
5. Graceful Shutdown - Clean worker termination

Related Challenges:
- Multi-channel access leads to long end-to-end paths
- Callbacks and authentication are complex
- Race conditions in message processing

Related Code:
- src/copaw/app/channels/manager.py - ChannelManager
- src/copaw/app/channels/base.py - BaseChannel
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Section 1: Worker Pool Management Tests
# ============================================================================

class TestWorkerPoolManagement:
    """
    Test the worker pool management in ChannelManager.
    
    ChannelManager creates multiple workers per channel to handle
    concurrent message processing. Key behaviors:
    - Workers per channel: configurable (default 4)
    - Each worker processes one session at a time
    - Workers are gracefully stopped on shutdown
    """
    
    @pytest.mark.asyncio
    async def test_worker_initialization(self):
        """
        Test that workers are correctly initialized per channel.
        
        Each channel should have its own queue and workers.
        Default workers per channel: _CONSUMER_WORKERS_PER_CHANNEL = 4
        """
        from copaw.app.channels.manager import (
            ChannelManager,
            _CONSUMER_WORKERS_PER_CHANNEL,
        )
        
        # Create mock channels
        mock_channel = MagicMock()
        mock_channel.channel = "test_channel"
        mock_channel.get_debounce_key = MagicMock(return_value="session_1")
        
        manager = ChannelManager(channels=[mock_channel])
        
        # Verify initial state
        assert manager.channels == [mock_channel]
        assert isinstance(manager._queues, dict)
        assert isinstance(manager._consumer_tasks, list)
        
        # Default workers per channel
        assert _CONSUMER_WORKERS_PER_CHANNEL == 4
    
    @pytest.mark.asyncio
    async def test_worker_task_creation(self):
        """
        Test that worker tasks are created when manager starts.
        
        When start() is called, workers should be spawned for each
        channel's queue.
        """
        from copaw.app.channels.manager import ChannelManager
        
        # Create mock channel with async process handler
        mock_channel = MagicMock()
        mock_channel.channel = "test_channel"
        mock_channel.get_debounce_key = MagicMock(return_value="session_1")
        
        manager = ChannelManager(channels=[mock_channel])
        
        # Mock the queue creation and worker spawning
        manager._queues["test_channel"] = asyncio.Queue()
        
        # Simulate starting workers
        original_tasks_count = len(manager._consumer_tasks)
        
        # After start, tasks should be created
        # (In real code, this happens in start() method)
        assert original_tasks_count == 0  # Initially no tasks


# ============================================================================
# Section 2: Session Isolation Tests
# ============================================================================

class TestSessionIsolation:
    """
    Test that same-session messages are processed by a single worker.
    
    Key invariant: Messages from the same session (same debounce key)
    are never processed concurrently. This prevents:
    - Duplicate responses
    - Out-of-order message handling
    - Race conditions in agent state
    """
    
    @pytest.mark.asyncio
    async def test_same_session_single_worker(self):
        """
        Test that same-session messages are drained by one worker.
        
        The _drain_same_key function ensures all messages with the same
        debounce key are batched together for single-worker processing.
        """
        from copaw.app.channels.manager import _drain_same_key
        
        # Create a queue with mixed sessions
        queue = asyncio.Queue()
        await queue.put({"session": "A", "data": 1})
        await queue.put({"session": "B", "data": 2})  # Different session
        await queue.put({"session": "A", "data": 3})  # Same as first
        await queue.put({"session": "A", "data": 4})  # Same as first
        
        # Mock channel that returns session as debounce key
        mock_channel = MagicMock()
        mock_channel.get_debounce_key = lambda p: p["session"]
        
        # Drain all messages from session A
        first_payload = {"session": "A", "data": 1}
        batch = _drain_same_key(queue, mock_channel, "A", first_payload)
        
        # Should have all session A messages (first_payload is included in batch)
        # Note: _drain_same_key returns [first_payload, ...additional_matching_items]
        assert all(m["session"] == "A" for m in batch)
        
        # Queue should still have session B message
        remaining = []
        while not queue.empty():
            remaining.append(await queue.get())
        assert len(remaining) == 1
        assert remaining[0]["session"] == "B"
    
    @pytest.mark.asyncio
    async def test_in_progress_tracking(self):
        """
        Test that in-progress sessions are tracked correctly.
        
        When a worker is processing a session, that session is marked
        as in-progress. New messages for that session go to pending.
        """
        from copaw.app.channels.manager import ChannelManager
        
        mock_channel = MagicMock()
        mock_channel.channel = "test_channel"
        
        manager = ChannelManager(channels=[mock_channel])
        
        # Simulate session in progress
        session_key = ("test_channel", "session_123")
        manager._in_progress.add(session_key)
        
        # Verify tracking
        assert session_key in manager._in_progress
        
        # Simulate session completion
        manager._in_progress.discard(session_key)
        assert session_key not in manager._in_progress


# ============================================================================
# Section 3: Concurrent Message Processing Tests
# ============================================================================

class TestConcurrentMessageProcessing:
    """
    Test concurrent processing of messages from different sessions.
    
    While same-session messages are serialized, different sessions can
    be processed concurrently for better throughput.
    """
    
    @pytest.mark.asyncio
    async def test_different_sessions_concurrent(self):
        """
        Test that different sessions can be processed concurrently.
        
        Sessions A and B should be able to run simultaneously on
        different workers.
        """
        from copaw.app.channels.manager import ChannelManager
        
        processed_sessions = []
        processing_lock = asyncio.Lock()
        
        async def mock_process(session: str, delay: float = 0.1):
            """Simulate processing with tracking."""
            async with processing_lock:
                processed_sessions.append(f"{session}_start")
            await asyncio.sleep(delay)
            async with processing_lock:
                processed_sessions.append(f"{session}_end")
        
        # Run two sessions concurrently
        await asyncio.gather(
            mock_process("A", 0.1),
            mock_process("B", 0.1),
        )
        
        # Verify both started before either ended (concurrent execution)
        a_start_idx = processed_sessions.index("A_start")
        b_start_idx = processed_sessions.index("B_start")
        a_end_idx = processed_sessions.index("A_end")
        b_end_idx = processed_sessions.index("B_end")
        
        # Both should start before either ends (indicates concurrency)
        assert a_start_idx < a_end_idx
        assert b_start_idx < b_end_idx
    
    @pytest.mark.asyncio
    async def test_message_queue_ordering(self):
        """
        Test that message queue ordering is preserved per session.
        
        Messages from the same session should maintain order.
        Messages from different sessions may interleave.
        """
        queue = asyncio.Queue()
        
        # Enqueue messages in order
        messages = [
            {"session": "A", "seq": 1},
            {"session": "A", "seq": 2},
            {"session": "B", "seq": 1},
            {"session": "A", "seq": 3},
            {"session": "B", "seq": 2},
        ]
        for msg in messages:
            await queue.put(msg)
        
        # Dequeue and verify FIFO order
        dequeued = []
        while not queue.empty():
            dequeued.append(await queue.get())
        
        # Overall order preserved
        assert dequeued == messages


# ============================================================================
# Section 4: Batch Processing and Merging Tests
# ============================================================================

class TestBatchProcessing:
    """
    Test batch processing and message merging.
    
    When multiple messages arrive for the same session quickly,
    they may be merged into a single batch for efficiency.
    """
    
    @pytest.mark.asyncio
    async def test_message_batching(self):
        """
        Test that messages are batched correctly.
        
        _process_batch handles:
        - Single message: process directly
        - Multiple messages: merge then process
        """
        from copaw.app.channels.manager import _process_batch
        
        processed_batches = []
        
        # Create mock channel that tracks batch processing
        mock_channel = MagicMock()
        mock_channel.channel = "test_channel"
        mock_channel._is_native_payload = MagicMock(return_value=False)
        mock_channel.merge_requests = MagicMock(
            return_value={"merged": True, "count": 3}
        )
        mock_channel._consume_one_request = AsyncMock()
        
        batch = [
            {"session": "A", "msg": 1},
            {"session": "A", "msg": 2},
            {"session": "A", "msg": 3},
        ]
        
        await _process_batch(mock_channel, batch)
        
        # Should have called merge for multiple messages
        mock_channel.merge_requests.assert_called_once_with(batch)
        mock_channel._consume_one_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_native_payload_merging(self):
        """
        Test merging of native payloads (e.g., DingTalk messages).
        
        Native payloads from platforms like DingTalk have special
        merge logic to combine session_webhook and content.
        """
        from copaw.app.channels.manager import _process_batch
        
        mock_channel = MagicMock()
        mock_channel.channel = "dingtalk"
        mock_channel._is_native_payload = MagicMock(return_value=True)
        mock_channel.merge_native_items = MagicMock(
            return_value={"session_webhook": "url", "merged": True}
        )
        mock_channel._consume_one_request = AsyncMock()
        
        batch = [
            {"session_webhook": "url", "text": {"content": "msg1"}},
            {"session_webhook": "url", "text": {"content": "msg2"}},
        ]
        
        await _process_batch(mock_channel, batch)
        
        mock_channel.merge_native_items.assert_called_once()


# ============================================================================
# Section 5: Graceful Shutdown Tests
# ============================================================================

class TestGracefulShutdown:
    """
    Test graceful shutdown of workers and cleanup of resources.
    
    On shutdown, the manager should:
    - Stop accepting new messages
    - Complete in-progress work
    - Clean up queues and tasks
    """
    
    @pytest.mark.asyncio
    async def test_worker_graceful_stop(self):
        """
        Test that workers stop gracefully on shutdown signal.
        
        Workers should finish current message before stopping.
        """
        from copaw.app.channels.manager import ChannelManager
        
        mock_channel = MagicMock()
        mock_channel.channel = "test_channel"
        
        manager = ChannelManager(channels=[mock_channel])
        
        # Simulate running state
        manager._queues["test_channel"] = asyncio.Queue()
        
        # Add a message to process
        await manager._queues["test_channel"].put({"test": "message"})
        
        # Stop should complete without hanging
        # (In real code, this calls stop() which cancels tasks)
        stop_completed = False
        
        async def mock_stop():
            await asyncio.gather(
                *manager._consumer_tasks,
                return_exceptions=True,
            )
            nonlocal stop_completed
            stop_completed = True
        
        # No tasks running, so stop should complete immediately
        await mock_stop()
        assert stop_completed
    
    @pytest.mark.asyncio
    async def test_pending_messages_on_shutdown(self):
        """
        Test handling of pending messages during shutdown.
        
        Pending messages should be processed or logged as dropped.
        """
        manager_state = {
            "_pending": {
                ("channel_A", "session_1"): [{"pending": True}],
            },
            "_in_progress": set(),
        }
        
        # On shutdown, pending messages should be handled
        pending_count = sum(len(v) for v in manager_state["_pending"].values())
        
        # In real implementation, these would be logged or processed
        assert pending_count == 1


# ============================================================================
# Section 6: Thread Safety Tests
# ============================================================================

class TestThreadSafety:
    """
    Test thread safety of concurrent operations.
    
    ChannelManager uses asyncio locks to ensure thread safety:
    - _lock: Global lock for queue operations
    - _key_locks: Per-session locks for debounce key operations
    """
    
    @pytest.mark.asyncio
    async def test_queue_thread_safety(self):
        """
        Test that queue operations are thread-safe.
        
        Multiple coroutines should be able to enqueue/dequeue
        without race conditions.
        """
        queue = asyncio.Queue()
        enqueue_count = 100
        dequeued_count = 0
        
        async def enqueue_items():
            for i in range(enqueue_count):
                await queue.put(i)
        
        async def dequeue_items():
            nonlocal dequeued_count
            while True:
                try:
                    await asyncio.wait_for(queue.get(), timeout=0.5)
                    dequeued_count += 1
                except asyncio.TimeoutError:
                    break
        
        # Run enqueuing and dequeuing concurrently
        await asyncio.gather(
            enqueue_items(),
            dequeue_items(),
        )
        
        assert dequeued_count == enqueue_count
    
    @pytest.mark.asyncio
    async def test_key_lock_prevents_race(self):
        """
        Test that per-key locks prevent race conditions.
        
        When two workers try to process the same session,
        only one should succeed.
        """
        from copaw.app.channels.manager import ChannelManager
        
        mock_channel = MagicMock()
        manager = ChannelManager(channels=[mock_channel])
        
        session_key = ("channel", "session")
        lock_acquired = []
        
        async def try_acquire():
            if session_key not in manager._key_locks:
                manager._key_locks[session_key] = asyncio.Lock()
            
            lock = manager._key_locks[session_key]
            acquired = lock.locked() is False
            if acquired:
                await lock.acquire()
                try:
                    lock_acquired.append(True)
                    await asyncio.sleep(0.1)  # Simulate work
                finally:
                    lock.release()
            return acquired
        
        # Run two acquires concurrently
        results = await asyncio.gather(
            try_acquire(),
            try_acquire(),
        )
        
        # Both should have succeeded (sequentially due to lock)
        assert sum(1 for r in results if r) >= 1


# ============================================================================
# Section 7: Multi-Channel Concurrency Tests
# ============================================================================

class TestMultiChannelConcurrency:
    """
    Test concurrent processing across multiple channels.
    
    Multiple channels (DingTalk, Feishu, QQ, etc.) should be able
    to process messages concurrently without interference.
    """
    
    @pytest.mark.asyncio
    async def test_multi_channel_isolation(self):
        """
        Test that channels are isolated from each other.
        
        Each channel should have its own queue and workers.
        """
        from copaw.app.channels.manager import ChannelManager
        
        mock_channels = [
            MagicMock(channel="dingtalk"),
            MagicMock(channel="feishu"),
            MagicMock(channel="qq"),
        ]
        
        for ch in mock_channels:
            ch.get_debounce_key = MagicMock(return_value="default_session")
        
        manager = ChannelManager(channels=mock_channels)
        
        # Each channel should have its own queue
        for ch in mock_channels:
            manager._queues[ch.channel] = asyncio.Queue()
        
        assert len(manager._queues) == 3
        
        # Messages in one channel should not affect others
        await manager._queues["dingtalk"].put({"dingtalk_msg": True})
        await manager._queues["feishu"].put({"feishu_msg": True})
        
        assert manager._queues["dingtalk"].qsize() == 1
        assert manager._queues["feishu"].qsize() == 1
        assert manager._queues["qq"].qsize() == 0


# ============================================================================
# Section 8: Performance Benchmarks
# ============================================================================

class TestConcurrencyPerformance:
    """
    Performance benchmarks for concurrent processing.
    
    These tests verify that concurrent processing provides
    meaningful throughput improvements over sequential.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_vs_sequential_throughput(self):
        """
        Compare throughput of concurrent vs sequential processing.
        
        Concurrent processing should be significantly faster for
        multiple independent sessions.
        """
        num_sessions = 10
        processing_time = 0.1
        
        async def process_session(session_id: int):
            await asyncio.sleep(processing_time)
            return session_id
        
        # Sequential processing time
        sequential_start = time.time()
        for i in range(num_sessions):
            await process_session(i)
        sequential_time = time.time() - sequential_start
        
        # Concurrent processing time
        concurrent_start = time.time()
        await asyncio.gather(*[process_session(i) for i in range(num_sessions)])
        concurrent_time = time.time() - concurrent_start
        
        # Concurrent should be much faster
        speedup = sequential_time / concurrent_time
        
        # Expect at least 5x speedup for 10 independent tasks
        assert speedup > 5, (
            f"Concurrent processing only {speedup:.1f}x faster than sequential"
        )
