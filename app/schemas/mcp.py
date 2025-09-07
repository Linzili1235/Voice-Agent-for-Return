# MCP (Model Context Protocol) 相关数据模式 - 定义与 MCP 服务交互的数据结构
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .base import IdempotencyRequest


class MCPToolRequest(IdempotencyRequest):
    """Request model for MCP tool execution."""
    
    tool_name: str = Field(..., description="Name of the MCP tool to execute", min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class MCPToolResponse(BaseModel):
    """Response model for MCP tool execution."""
    
    tool_name: str = Field(description="Executed tool name")
    success: bool = Field(description="Whether tool execution was successful")
    result: Optional[Any] = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    execution_time: float = Field(description="Tool execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")


class MCPAgentRequest(IdempotencyRequest):
    """Request model for MCP agent interaction."""
    
    message: str = Field(..., description="Message to send to the agent", min_length=1)
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class MCPAgentResponse(BaseModel):
    """Response model for MCP agent interaction."""
    
    response: str = Field(description="Agent response message")
    session_id: str = Field(description="Session identifier")
    tools_used: List[str] = Field(default_factory=list, description="Tools used during interaction")
    execution_time: float = Field(description="Interaction execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
