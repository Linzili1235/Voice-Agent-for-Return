# MCP 服务模块 - 处理与 MCP 服务器的交互
import time
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException, status

from app.config.settings import settings
from app.schemas.mcp import MCPToolRequest, MCPToolResponse, MCPAgentRequest, MCPAgentResponse
from app.utils.logging import get_logger, log_external_api_call


logger = get_logger(__name__)


class MCPService:
    """Service for interacting with MCP (Model Context Protocol) server."""
    
    def __init__(self):
        self.base_url = settings.mcp_server_url
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def execute_tool(self, request: MCPToolRequest) -> MCPToolResponse:
        """
        Execute a tool via MCP server.
        Makes idempotent request to MCP server.
        """
        payload = {
            "toolName": request.tool_name,
            "parameters": request.parameters,
            "context": request.context or {}
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/tools/execute",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response_time = time.time() - start_time
                
                log_external_api_call(
                    logger=logger,
                    service="mcp",
                    endpoint="/tools/execute",
                    method="POST",
                    status_code=response.status_code,
                    response_time=response_time,
                    error=None if response.is_success else response.text
                )
                
                if response.is_success:
                    data = response.json()
                    return MCPToolResponse(
                        tool_name=request.tool_name,
                        success=data.get("success", True),
                        result=data.get("result"),
                        error=data.get("error"),
                        execution_time=response_time,
                        timestamp=data.get("timestamp")
                    )
                else:
                    return MCPToolResponse(
                        tool_name=request.tool_name,
                        success=False,
                        result=None,
                        error=f"MCP API error: {response.text}",
                        execution_time=response_time
                    )
        
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="mcp",
                endpoint="/tools/execute",
                method="POST",
                status_code=408,
                response_time=response_time,
                error="Request timeout"
            )
            return MCPToolResponse(
                tool_name=request.tool_name,
                success=False,
                result=None,
                error="MCP API request timeout",
                execution_time=response_time
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="mcp",
                endpoint="/tools/execute",
                method="POST",
                status_code=500,
                response_time=response_time,
                error=str(e)
            )
            return MCPToolResponse(
                tool_name=request.tool_name,
                success=False,
                result=None,
                error=f"Internal error: {str(e)}",
                execution_time=response_time
            )
    
    async def interact_with_agent(self, request: MCPAgentRequest) -> MCPAgentResponse:
        """Interact with MCP agent."""
        payload = {
            "message": request.message,
            "sessionId": request.session_id,
            "context": request.context or {}
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/agent/interact",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response_time = time.time() - start_time
                
                log_external_api_call(
                    logger=logger,
                    service="mcp",
                    endpoint="/agent/interact",
                    method="POST",
                    status_code=response.status_code,
                    response_time=response_time,
                    error=None if response.is_success else response.text
                )
                
                if response.is_success:
                    data = response.json()
                    return MCPAgentResponse(
                        response=data.get("response", ""),
                        session_id=data.get("sessionId", request.session_id or "default"),
                        tools_used=data.get("toolsUsed", []),
                        execution_time=response_time,
                        timestamp=data.get("timestamp")
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"MCP API error: {response.text}"
                    )
        
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="mcp",
                endpoint="/agent/interact",
                method="POST",
                status_code=408,
                response_time=response_time,
                error="Request timeout"
            )
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="MCP API request timeout"
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            log_external_api_call(
                logger=logger,
                service="mcp",
                endpoint="/agent/interact",
                method="POST",
                status_code=500,
                response_time=response_time,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {str(e)}"
            )


# Global service instance
mcp_service = MCPService()
