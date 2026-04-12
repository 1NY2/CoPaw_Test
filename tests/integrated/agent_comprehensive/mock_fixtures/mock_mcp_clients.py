# -*- coding: utf-8 -*-
"""
Mock MCP (Model Context Protocol) clients for testing tool integration.

This module provides mock implementations of MCP clients that simulate
MCP server connections and tool discovery without real external servers.

Key Features:
- Simulate MCP server lifecycle (initialize, connect, disconnect)
- Mock tool discovery and registration
- Track tool calls for verification
- Support for multiple tools per client

MCP Protocol Overview:
- MCP clients connect to MCP servers (via stdio, HTTP, or SSE)
- Servers expose tools with schemas (name, description, parameters)
- Clients can call tools with arguments and receive results
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class MockMCPToolSchema:
    """
    Schema for an MCP tool.
    
    This defines the structure of a tool exposed by an MCP server.
    
    Attributes:
        name: Unique name of the tool
        description: Human-readable description
        parameters: JSON Schema for tool parameters
    """
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP protocol format."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
            },
        }


@dataclass
class MockMCPToolResult:
    """
    Result from calling an MCP tool.
    
    Attributes:
        content: The result content (usually a list of content blocks)
        is_error: Whether the result is an error
        timestamp: When the result was generated
    """
    content: List[Dict[str, Any]]
    is_error: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP protocol format."""
        return {
            "content": self.content,
            "isError": self.is_error,
        }


@dataclass
class MockMCPToolCall:
    """
    Record of an MCP tool call.
    
    This tracks when a tool was called and with what arguments.
    
    Attributes:
        tool_name: Name of the tool called
        arguments: Arguments passed to the tool
        result: Result returned by the tool
        timestamp: When the call was made
    """
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[MockMCPToolResult] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MockMCPTool:
    """
    Mock MCP tool that can be registered with a MockMCPClient.
    
    This simulates a tool exposed by an MCP server, including its
    schema and execution behavior.
    
    Example:
        >>> tool = MockMCPTool(
        ...     name="read_file",
        ...     description="Read a file from the filesystem",
        ...     parameters={
        ...         "path": {"type": "string", "description": "File path"}
        ...     },
        ...     handler=lambda args: {"content": f"File content: {args['path']}"}
        ... )
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        handler: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ):
        """
        Initialize a mock MCP tool.
        
        Args:
            name: Unique tool name
            description: Human-readable description
            parameters: JSON Schema for parameters
            handler: Function to handle tool calls (receives args dict)
        """
        self.schema = MockMCPToolSchema(
            name=name,
            description=description,
            parameters=parameters or {},
        )
        self.handler = handler or self._default_handler
        self.call_count = 0
        self.call_history: List[MockMCPToolCall] = []
    
    def _default_handler(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler that returns the arguments."""
        return {"echo": arguments}
    
    def __call__(self, arguments: Dict[str, Any]) -> MockMCPToolResult:
        """
        Call the tool with the given arguments.
        
        Args:
            arguments: Dictionary of arguments for the tool
        
        Returns:
            MockMCPToolResult with the tool's output
        """
        self.call_count += 1
        call_record = MockMCPToolCall(
            tool_name=self.schema.name,
            arguments=arguments,
        )
        
        try:
            result = self.handler(arguments)
            
            # Convert result to MCP content format
            if isinstance(result, dict):
                content = [{"type": "text", "text": json.dumps(result)}]
            elif isinstance(result, str):
                content = [{"type": "text", "text": result}]
            elif isinstance(result, list):
                content = result
            else:
                content = [{"type": "text", "text": str(result)}]
            
            call_record.result = MockMCPToolResult(content=content)
            
        except Exception as e:
            call_record.result = MockMCPToolResult(
                content=[{"type": "text", "text": f"Error: {e}"}],
                is_error=True,
            )
        
        self.call_history.append(call_record)
        return call_record.result


class MockMCPClient:
    """
    Mock MCP client for testing MCP tool integration.
    
    This simulates an MCP client that connects to an MCP server and
    provides access to its tools. It tracks all interactions for
    verification in tests.
    
    Lifecycle:
    1. Create client with configuration
    2. Call initialize() to simulate server handshake
    3. Discover and register tools
    4. Call tools with arguments
    5. Call close() to disconnect
    
    Example:
        >>> client = MockMCPClient(name="filesystem")
        >>> client.add_tool(MockMCPTool(
        ...     name="read_file",
        ...     handler=lambda args: {"content": "Hello"}
        ... ))
        >>> await client.initialize()
        >>> tools = await client.list_tools()
        >>> result = await client.call_tool("read_file", {"path": "/tmp/test.txt"})
    """
    
    def __init__(
        self,
        name: str = "mock_mcp_client",
        description: str = "Mock MCP client for testing",
        enabled: bool = True,
        transport: str = "stdio",
        command: str = "mock_command",
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the mock MCP client.
        
        Args:
            name: Unique client name
            description: Human-readable description
            enabled: Whether this client is enabled
            transport: Transport type ("stdio", "streamable_http", "sse")
            command: Command to run (for stdio transport)
            args: Command arguments
            env: Environment variables
        """
        self.name = name
        self.description = description
        self.enabled = enabled
        self.transport = transport
        self.command = command
        self.args = args or []
        self.env = env or {}
        
        # Tools registry
        self._tools: Dict[str, MockMCPTool] = {}
        
        # State tracking
        self._initialized = False
        self._connected = False
        self.initialize_count = 0
        self.close_count = 0
    
    def add_tool(self, tool: MockMCPTool) -> None:
        """
        Add a tool to this client.
        
        Args:
            tool: MockMCPTool to add
        """
        self._tools[tool.schema.name] = tool
    
    def add_simple_tool(
        self,
        name: str,
        description: str = "",
        result: Any = None,
    ) -> MockMCPTool:
        """
        Add a simple tool that returns a fixed result.
        
        Args:
            name: Tool name
            description: Tool description
            result: Value to return when called
        
        Returns:
            The created MockMCPTool
        """
        def handler(args):
            return result or {"status": "ok", "args": args}
        
        tool = MockMCPTool(
            name=name,
            description=description,
            handler=handler,
        )
        self.add_tool(tool)
        return tool
    
    @property
    def tools(self) -> Dict[str, MockMCPTool]:
        """Get the tools dictionary."""
        return self._tools
    
    def get_tool(self, name: str) -> Optional[MockMCPTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
        
        Returns:
            MockMCPTool or None if not found
        """
        return self._tools.get(name)
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the MCP client (simulate server handshake).
        
        This simulates the MCP initialize handshake that exchanges
        capabilities between client and server.
        
        Returns:
            Server capabilities
        """
        self.initialize_count += 1
        self._initialized = True
        self._connected = True
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
            },
            "serverInfo": {
                "name": self.name,
                "version": "1.0.0",
            },
        }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all tools available from this client.
        
        Returns:
            List of tool schemas in MCP format
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        return [tool.schema.to_mcp_format() for tool in self._tools.values()]
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> MockMCPToolResult:
        """
        Call a tool with the given arguments.
        
        Args:
            name: Tool name
            arguments: Arguments for the tool
        
        Returns:
            MockMCPToolResult from the tool execution
        
        Raises:
            ValueError: If tool not found
            RuntimeError: If client not initialized
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized")
        
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        # Simulate async tool call
        await asyncio.sleep(0.001)
        
        return tool(arguments)
    
    async def close(self) -> None:
        """Close the MCP client connection."""
        self.close_count += 1
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected and self._initialized
    
    def get_tool_call_count(self, tool_name: str) -> int:
        """
        Get the number of times a specific tool was called.
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Number of calls
        """
        tool = self._tools.get(tool_name)
        return tool.call_count if tool else 0
    
    def get_all_tool_calls(self) -> List[MockMCPToolCall]:
        """
        Get all tool calls across all tools.
        
        Returns:
            List of all MockMCPToolCall records
        """
        calls = []
        for tool in self._tools.values():
            calls.extend(tool.call_history)
        return sorted(calls, key=lambda x: x.timestamp)
    
    def reset(self) -> None:
        """Reset the client state."""
        self._initialized = False
        self._connected = False
        for tool in self._tools.values():
            tool.call_count = 0
            tool.call_history.clear()


def create_filesystem_mcp_client() -> MockMCPClient:
    """
    Create a mock filesystem MCP client.
    
    This creates a client with typical filesystem tools for testing.
    
    Returns:
        MockMCPClient configured with filesystem tools
    """
    client = MockMCPClient(
        name="filesystem",
        description="Mock filesystem MCP client",
    )
    
    def read_file_handler(args):
        path = args.get("path", "/unknown")
        return {"content": f"Mock content of {path}"}
    
    def write_file_handler(args):
        path = args.get("path", "/unknown")
        content = args.get("content", "")
        return {"success": True, "bytes_written": len(content)}
    
    def list_directory_handler(args):
        path = args.get("path", "/")
        return {"entries": ["file1.txt", "file2.txt", "subdir/"]}
    
    client.add_tool(MockMCPTool(
        name="read_file",
        description="Read a file from the filesystem",
        parameters={"path": {"type": "string", "description": "File path"}},
        handler=read_file_handler,
    ))
    
    client.add_tool(MockMCPTool(
        name="write_file",
        description="Write content to a file",
        parameters={
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        handler=write_file_handler,
    ))
    
    client.add_tool(MockMCPTool(
        name="list_directory",
        description="List contents of a directory",
        parameters={"path": {"type": "string"}},
        handler=list_directory_handler,
    ))
    
    return client


def create_weather_mcp_client() -> MockMCPClient:
    """
    Create a mock weather MCP client.
    
    This creates a client with weather-related tools for testing.
    
    Returns:
        MockMCPClient configured with weather tools
    """
    client = MockMCPClient(
        name="weather",
        description="Mock weather MCP client",
    )
    
    def get_weather_handler(args):
        location = args.get("location", "Unknown")
        return {
            "location": location,
            "temperature": "22°C",
            "condition": "Sunny",
            "humidity": "45%",
        }
    
    client.add_tool(MockMCPTool(
        name="get_weather",
        description="Get current weather for a location",
        parameters={
            "location": {
                "type": "string",
                "description": "City name or coordinates",
            },
        },
        handler=get_weather_handler,
    ))
    
    return client
