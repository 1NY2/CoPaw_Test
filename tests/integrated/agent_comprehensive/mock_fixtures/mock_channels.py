# -*- coding: utf-8 -*-
"""
Mock Channel implementations for testing message processing.

This module provides mock implementations of the channel classes (DingTalk, QQ)
that simulate message receiving and sending without real external connections.

Key Features:
- Simulate message reception from various channels
- Track sent messages for verification
- Simulate WebSocket/HTTP connections
- Test channel initialization and lifecycle
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest, Event

logger = logging.getLogger(__name__)


@dataclass
class MockMessage:
    """
    Mock message received from a channel.
    
    This represents a message that would be received from an external
    messaging platform like DingTalk or QQ.
    
    Attributes:
        content: Text content of the message
        sender_id: ID of the message sender
        session_id: Session/conversation ID
        channel: Channel type (e.g., "dingtalk", "qq")
        timestamp: When the message was received
        metadata: Additional metadata (e.g., group info, attachments)
    """
    content: str
    sender_id: str
    session_id: str
    channel: str = "mock"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MockReply:
    """
    Mock reply sent through a channel.
    
    This tracks messages that the agent sends back through the channel.
    
    Attributes:
        content: Text content of the reply
        recipient_id: ID of the recipient
        session_id: Session/conversation ID
        timestamp: When the reply was sent
    """
    content: str
    recipient_id: str
    session_id: str
    timestamp: datetime = field(default_factory=datetime.now)


class MockBaseChannel:
    """
    Base class for mock channels.
    
    This provides common functionality for mock channel implementations,
    including message tracking and lifecycle management.
    
    Attributes:
        channel: Channel identifier
        enabled: Whether the channel is enabled
        messages_received: List of messages received by this channel
        replies_sent: List of replies sent through this channel
    """
    
    channel: str = "mock"
    
    def __init__(
        self,
        enabled: bool = True,
        bot_prefix: str = "[BOT]",
        show_tool_details: bool = True,
    ):
        """
        Initialize the mock channel.
        
        Args:
            enabled: Whether this channel is enabled
            bot_prefix: Prefix for bot messages
            show_tool_details: Whether to show tool details in messages
        """
        self.enabled = enabled
        self.bot_prefix = bot_prefix
        self.show_tool_details = show_tool_details
        
        # Message tracking
        self.messages_received: List[MockMessage] = []
        self.replies_sent: List[MockReply] = []
        
        # Lifecycle state
        self._started = False
        self._stopped = False
        
        # Callback for processing messages (set by manager)
        self._process: Optional[Callable] = None
        self._enqueue: Optional[Callable] = None
    
    def set_process_handler(self, handler: Callable) -> None:
        """
        Set the message processing handler.
        
        Args:
            handler: Async function that processes AgentRequest and yields Events
        """
        self._process = handler
    
    def set_enqueue_callback(self, callback: Callable) -> None:
        """
        Set the enqueue callback for incoming messages.
        
        Args:
            callback: Function to call when a message is received
        """
        self._enqueue = callback
    
    def receive_message(
        self,
        content: str,
        sender_id: str = "test_user",
        session_id: str = "test_session",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MockMessage:
        """
        Simulate receiving a message.
        
        This creates a MockMessage and adds it to the received messages list.
        Use this in tests to simulate incoming messages.
        
        Args:
            content: Text content of the message
            sender_id: ID of the sender
            session_id: Session/conversation ID
            metadata: Additional metadata
        
        Returns:
            The created MockMessage
        """
        message = MockMessage(
            content=content,
            sender_id=sender_id,
            session_id=session_id,
            channel=self.channel,
            metadata=metadata or {},
        )
        self.messages_received.append(message)
        
        # Trigger enqueue if callback is set
        if self._enqueue:
            self._enqueue(self._create_agent_request(message))
        
        return message
    
    def _create_agent_request(self, message: MockMessage) -> Dict[str, Any]:
        """
        Create an AgentRequest-like dict from a MockMessage.
        
        Args:
            message: The mock message
        
        Returns:
            Dictionary representing an AgentRequest
        """
        from agentscope_runtime.engine.schemas.agent_schemas import ContentType, TextContent
        
        return {
            "channel_id": message.channel,
            "sender_id": message.sender_id,
            "session_id": message.session_id,
            "content_parts": [
                TextContent(
                    type=ContentType.TEXT,
                    text=message.content,
                ),
            ],
            "meta": message.metadata,
        }
    
    def send_reply(
        self,
        content: str,
        recipient_id: str,
        session_id: str,
    ) -> MockReply:
        """
        Simulate sending a reply.
        
        This creates a MockReply and adds it to the sent replies list.
        
        Args:
            content: Text content of the reply
            recipient_id: ID of the recipient
            session_id: Session/conversation ID
        
        Returns:
            The created MockReply
        """
        reply = MockReply(
            content=content,
            recipient_id=recipient_id,
            session_id=session_id,
        )
        self.replies_sent.append(reply)
        return reply
    
    async def start(self) -> None:
        """Start the mock channel."""
        self._started = True
        logger.debug("Mock channel %s started", self.channel)
    
    async def stop(self) -> None:
        """Stop the mock channel."""
        self._stopped = True
        logger.debug("Mock channel %s stopped", self.channel)
    
    def is_running(self) -> bool:
        """Check if the channel is running."""
        return self._started and not self._stopped
    
    def clear_messages(self) -> None:
        """Clear all tracked messages."""
        self.messages_received.clear()
        self.replies_sent.clear()


class MockDingTalkChannel(MockBaseChannel):
    """
    Mock DingTalk channel for testing.
    
    This simulates a DingTalk channel with realistic message structures
    and behaviors.
    
    DingTalk Specific Features:
    - Stream mode for receiving messages
    - Webhook for sending messages
    - Support for rich text and media
    
    Example:
        >>> channel = MockDingTalkChannel()
        >>> channel.receive_message(
        ...     content="Hello bot!",
        ...     sender_id="user123",
        ...     session_id="conv456",
        ... )
        >>> assert len(channel.messages_received) == 1
    """
    
    channel = "dingtalk"
    
    def __init__(
        self,
        client_id: str = "mock_client_id",
        client_secret: str = "mock_client_secret",
        **kwargs,
    ):
        """
        Initialize the mock DingTalk channel.
        
        Args:
            client_id: Mock DingTalk Client ID
            client_secret: Mock DingTalk Client Secret
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(**kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
    
    def receive_dingtalk_message(
        self,
        content: str,
        sender_id: str = "dingtalk_user",
        session_id: str = "dingtalk_session",
        conversation_type: str = "private",  # "private" or "group"
        conversation_id: Optional[str] = None,
    ) -> MockMessage:
        """
        Simulate receiving a DingTalk message.
        
        Args:
            content: Message content
            sender_id: Sender's DingTalk user ID
            session_id: Session ID
            conversation_type: "private" for direct message, "group" for group
            conversation_id: Conversation ID (required for group messages)
        
        Returns:
            MockMessage with DingTalk-specific metadata
        """
        metadata = {
            "conversation_type": conversation_type,
            "conversation_id": conversation_id or session_id,
        }
        return self.receive_message(
            content=content,
            sender_id=sender_id,
            session_id=session_id,
            metadata=metadata,
        )


class MockQQChannel(MockBaseChannel):
    """
    Mock QQ channel for testing.
    
    This simulates a QQ channel with realistic message structures
    and behaviors.
    
    QQ Specific Features:
    - Guild (server) based messaging
    - Direct messages
    - Group messages
    - WebSocket events
    
    Example:
        >>> channel = MockQQChannel()
        >>> channel.receive_qq_message(
        ...     content="@bot 你好",
        ...     sender_id="qq_user_123",
        ...     guild_id="guild_456",
        ... )
        >>> assert len(channel.messages_received) == 1
    """
    
    channel = "qq"
    
    def __init__(
        self,
        app_id: str = "mock_app_id",
        client_secret: str = "mock_client_secret",
        **kwargs,
    ):
        """
        Initialize the mock QQ channel.
        
        Args:
            app_id: Mock QQ App ID
            client_secret: Mock QQ Client Secret
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(**kwargs)
        self.app_id = app_id
        self.client_secret = client_secret
    
    def receive_qq_message(
        self,
        content: str,
        sender_id: str = "qq_user",
        session_id: str = "qq_session",
        message_type: str = "direct",  # "direct", "guild", "group"
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> MockMessage:
        """
        Simulate receiving a QQ message.
        
        Args:
            content: Message content
            sender_id: Sender's QQ user ID
            session_id: Session ID
            message_type: Type of message (direct, guild, group)
            guild_id: Guild ID for guild messages
            channel_id: Channel ID for guild messages
        
        Returns:
            MockMessage with QQ-specific metadata
        """
        metadata = {
            "message_type": message_type,
            "guild_id": guild_id,
            "channel_id": channel_id,
        }
        return self.receive_message(
            content=content,
            sender_id=sender_id,
            session_id=session_id,
            metadata=metadata,
        )


class MockChannelManager:
    """
    Mock channel manager for testing multi-channel scenarios.
    
    This manages multiple mock channels and provides a unified interface
    for testing channel interactions.
    
    Attributes:
        channels: Dictionary of channel name to MockBaseChannel
        started: Whether the manager has been started
    """
    
    def __init__(self):
        """Initialize the mock channel manager."""
        self.channels: Dict[str, MockBaseChannel] = {}
        self.started = False
        self._process_handler: Optional[Callable] = None
    
    def add_channel(self, channel: MockBaseChannel) -> None:
        """
        Add a channel to the manager.
        
        Args:
            channel: Mock channel to add
        """
        self.channels[channel.channel] = channel
    
    def get_channel(self, name: str) -> Optional[MockBaseChannel]:
        """
        Get a channel by name.
        
        Args:
            name: Channel name (e.g., "dingtalk", "qq")
        
        Returns:
            Mock channel or None if not found
        """
        return self.channels.get(name)
    
    def set_process_handler(self, handler: Callable) -> None:
        """
        Set the process handler for all channels.
        
        Args:
            handler: Async function to process messages
        """
        self._process_handler = handler
        for channel in self.channels.values():
            channel.set_process_handler(handler)
    
    async def start_all(self) -> None:
        """Start all channels."""
        for channel in self.channels.values():
            if channel.enabled:
                await channel.start()
        self.started = True
    
    async def stop_all(self) -> None:
        """Stop all channels."""
        for channel in self.channels.values():
            await channel.stop()
        self.started = False
    
    def receive_message(
        self,
        channel_name: str,
        content: str,
        sender_id: str = "test_user",
        session_id: str = "test_session",
        **kwargs,
    ) -> Optional[MockMessage]:
        """
        Receive a message on a specific channel.
        
        Args:
            channel_name: Name of the channel to receive on
            content: Message content
            sender_id: Sender ID
            session_id: Session ID
            **kwargs: Additional arguments for channel-specific methods
        
        Returns:
            MockMessage or None if channel not found
        """
        channel = self.channels.get(channel_name)
        if not channel:
            return None
        
        if channel_name == "dingtalk":
            return channel.receive_dingtalk_message(
                content=content,
                sender_id=sender_id,
                session_id=session_id,
                **kwargs,
            )
        elif channel_name == "qq":
            return channel.receive_qq_message(
                content=content,
                sender_id=sender_id,
                session_id=session_id,
                **kwargs,
            )
        else:
            return channel.receive_message(
                content=content,
                sender_id=sender_id,
                session_id=session_id,
            )
    
    def get_all_messages(self) -> Dict[str, List[MockMessage]]:
        """
        Get all messages received across all channels.
        
        Returns:
            Dictionary mapping channel names to message lists
        """
        return {
            name: channel.messages_received
            for name, channel in self.channels.items()
        }
    
    def get_all_replies(self) -> Dict[str, List[MockReply]]:
        """
        Get all replies sent across all channels.
        
        Returns:
            Dictionary mapping channel names to reply lists
        """
        return {
            name: channel.replies_sent
            for name, channel in self.channels.items()
        }
    
    def clear_all(self) -> None:
        """Clear all messages and replies from all channels."""
        for channel in self.channels.values():
            channel.clear_messages()
