# MCP API 测试 - 测试与 MCP 服务器交互的 API 端点
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.schemas.mcp import MCPToolResponse, MCPAgentResponse


def test_execute_tool_invalid_tool_name(client: TestClient, sample_mcp_tool_request):
    """Test executing a tool with invalid tool name."""
    invalid_request = sample_mcp_tool_request.copy()
    invalid_request["tool_name"] = ""  # Empty tool name
    
    response = client.post("/mcp/tools/execute", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_execute_tool_invalid_idempotency_key(client: TestClient, sample_mcp_tool_request):
    """Test executing a tool with invalid idempotency key."""
    invalid_request = sample_mcp_tool_request.copy()
    invalid_request["idempotency_key"] = ""  # Empty key
    
    response = client.post("/mcp/tools/execute", json=invalid_request)
    assert response.status_code == 422  # Validation error


@patch('app.services.mcp_service.mcp_service.execute_tool')
def test_execute_tool_success(mock_execute_tool, client: TestClient, sample_mcp_tool_request):
    """Test successful tool execution."""
    # Mock the service response
    mock_response = MCPToolResponse(
        tool_name="test_tool",
        success=True,
        result={"output": "test result"},
        error=None,
        execution_time=1.5,
        timestamp="2023-01-01T00:00:00Z"
    )
    mock_execute_tool.return_value = mock_response
    
    response = client.post("/mcp/tools/execute", json=sample_mcp_tool_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Tool executed successfully"
    assert data["data"]["tool_name"] == "test_tool"
    assert data["data"]["success"] is True


@patch('app.services.mcp_service.mcp_service.execute_tool')
def test_execute_tool_failure(mock_execute_tool, client: TestClient, sample_mcp_tool_request):
    """Test tool execution failure."""
    # Mock the service response for failure
    mock_response = MCPToolResponse(
        tool_name="test_tool",
        success=False,
        result=None,
        error="Tool execution failed",
        execution_time=1.0,
        timestamp="2023-01-01T00:00:00Z"
    )
    mock_execute_tool.return_value = mock_response
    
    response = client.post("/mcp/tools/execute", json=sample_mcp_tool_request)
    assert response.status_code == 200  # Service returns success even if tool fails
    
    data = response.json()
    assert data["success"] is True  # API call succeeded
    assert data["data"]["success"] is False  # But tool execution failed


def test_agent_interact_invalid_message(client: TestClient, sample_mcp_agent_request):
    """Test agent interaction with invalid message."""
    invalid_request = sample_mcp_agent_request.copy()
    invalid_request["message"] = ""  # Empty message
    
    response = client.post("/mcp/agent/interact", json=invalid_request)
    assert response.status_code == 422  # Validation error


@patch('app.services.mcp_service.mcp_service.interact_with_agent')
def test_agent_interact_success(mock_interact, client: TestClient, sample_mcp_agent_request):
    """Test successful agent interaction."""
    # Mock the service response
    mock_response = MCPAgentResponse(
        response="Hello! How can I help you?",
        session_id="session-123",
        tools_used=["tool1", "tool2"],
        execution_time=2.5,
        timestamp="2023-01-01T00:00:00Z"
    )
    mock_interact.return_value = mock_response
    
    response = client.post("/mcp/agent/interact", json=sample_mcp_agent_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Agent interaction completed successfully"
    assert data["data"]["response"] == "Hello! How can I help you?"
    assert data["data"]["session_id"] == "session-123"
    assert len(data["data"]["tools_used"]) == 2
