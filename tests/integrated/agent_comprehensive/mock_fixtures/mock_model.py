# -*- coding: utf-8 -*-
"""
Mock LLM Model for testing agent reasoning without real API calls.

This module provides mock model implementations that simulate LLM responses,
allowing tests to verify agent behavior without external API dependencies.

The mock model can be configured to return specific responses for specific
inputs, making it ideal for testing specific agent behaviors.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class MockModelResponse:
    """
    Mock response from LLM model.
    
    Attributes:
        content: The text content of the response
        tool_calls: Optional list of tool calls to include in the response
        finish_reason: Reason for finishing (e.g., "stop", "tool_calls")
    """
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "stop"


def create_mock_model_response(
    content: str = "",
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    finish_reason: str = "stop",
) -> MockModelResponse:
    """
    Create a mock model response with the given parameters.
    
    This is a convenience function for creating MockModelResponse objects.
    
    Args:
        content: Text content of the response
        tool_calls: Optional list of tool call dictionaries, each containing:
            - id: Unique identifier for the tool call
            - function: Dict with "name" and "arguments" keys
        finish_reason: Reason for finishing the response
    
    Returns:
        MockModelResponse object
    
    Example:
        >>> response = create_mock_model_response(
        ...     content="I will help you with that.",
        ...     tool_calls=[{
        ...         "id": "call_123",
        ...         "function": {
        ...             "name": "get_current_time",
        ...             "arguments": "{}"
        ...         }
        ...     }],
        ...     finish_reason="tool_calls"
        ... )
    """
    return MockModelResponse(
        content=content,
        tool_calls=tool_calls or [],
        finish_reason=finish_reason,
    )


class MockModelWrapper:
    """
    Mock wrapper that simulates LLM model behavior for testing.
    
    This class provides a mock implementation of the model wrapper used by
    CoPawAgent. It can be configured to return specific responses for specific
    inputs, or to follow a predefined sequence of responses.
    
    Key Features:
    - Predefined response sequences for testing multi-turn conversations
    - Tool call simulation for testing agent-tool interactions
    - Call tracking for verifying model invocations
    
    Usage Example:
        >>> mock_model = MockModelWrapper()
        >>> mock_model.add_response("Hello! How can I help you?")
        >>> mock_model.add_tool_call("get_current_time", {})
        >>> # Use in agent initialization
        
    Attributes:
        responses: Queue of responses to return
        call_history: List of all calls made to the model
        default_response: Default response when queue is empty
    """
    
    def __init__(
        self,
        default_response: str = "I understand. How can I help?",
    ):
        """
        Initialize the mock model wrapper.
        
        Args:
            default_response: Default text to return when no responses are queued
        """
        self.responses: List[MockModelResponse] = []
        self.call_history: List[Dict[str, Any]] = []
        self.default_response = default_response
        self._call_count = 0
    
    def add_response(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        finish_reason: str = "stop",
    ) -> "MockModelWrapper":
        """
        Add a response to the response queue.
        
        Responses are returned in FIFO order. If no responses are queued,
        the default response is used.
        
        Args:
            content: Text content of the response
            tool_calls: Optional list of tool call dictionaries
            finish_reason: Reason for finishing
        
        Returns:
            Self for method chaining
        
        Example:
            >>> model.add_response("Hello!").add_response("Goodbye!")
        """
        self.responses.append(create_mock_model_response(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        ))
        return self
    
    def add_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        call_id: Optional[str] = None,
    ) -> "MockModelWrapper":
        """
        Add a response that includes a tool call.
        
        This is a convenience method for adding tool call responses.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            call_id: Optional unique identifier (auto-generated if not provided)
        
        Returns:
            Self for method chaining
        """
        call_id = call_id or f"call_{self._call_count}"
        self._call_count += 1
        return self.add_response(
            content="",
            tool_calls=[{
                "id": call_id,
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(arguments),
                },
            }],
            finish_reason="tool_calls",
        )
    
    def get_next_response(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> MockModelResponse:
        """
        Get the next response from the queue.
        
        This method simulates calling the LLM model. It records the call
        in the history and returns the next queued response.
        
        Args:
            messages: Optional list of messages (recorded in call history)
        
        Returns:
            Next MockModelResponse from queue, or default response
        """
        self.call_history.append({
            "messages": messages,
            "response_index": len(self.call_history),
        })
        
        if self.responses:
            return self.responses.pop(0)
        return create_mock_model_response(self.default_response)
    
    def __call__(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> MockModelResponse:
        """
        Make the mock model callable for compatibility with agent code.
        
        Args:
            messages: List of messages to "process"
            **kwargs: Additional arguments (ignored)
        
        Returns:
            MockModelResponse
        """
        return self.get_next_response(messages)
    
    def clear_history(self) -> None:
        """Clear the call history."""
        self.call_history.clear()
    
    def reset(self) -> None:
        """Reset the mock model to initial state."""
        self.responses.clear()
        self.call_history.clear()
        self._call_count = 0
    
    @property
    def call_count(self) -> int:
        """Return the number of times the model has been called."""
        return len(self.call_history)
    
    def get_last_call_messages(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get the messages from the last model call.
        
        Returns:
            List of messages from last call, or None if no calls made
        """
        if self.call_history:
            return self.call_history[-1].get("messages")
        return None


class MockModelFormatter:
    """
    Mock formatter that formats messages for the model.
    
    This class simulates the message formatter used by CoPawAgent.
    It converts messages to the format expected by the model.
    """
    
    def format(
        self,
        messages: List[Any],
    ) -> List[Dict[str, Any]]:
        """
        Format messages for the mock model.
        
        Args:
            messages: List of message objects
        
        Returns:
            List of formatted message dictionaries
        """
        formatted = []
        for msg in messages:
            if hasattr(msg, "role") and hasattr(msg, "content"):
                formatted.append({
                    "role": msg.role,
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                })
            elif isinstance(msg, dict):
                formatted.append(msg)
            else:
                formatted.append({"role": "user", "content": str(msg)})
        return formatted
