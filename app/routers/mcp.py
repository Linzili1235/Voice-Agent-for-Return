# MCP API 路由 - 处理与 MCP 服务器交互的 API 端点
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.schemas.base import BaseResponse
from app.schemas.mcp import MCPToolRequest, MCPToolResponse, MCPAgentRequest, MCPAgentResponse
from app.services.mcp_service import mcp_service
from app.utils.cache import cache_manager
from app.utils.logging import get_logger, log_request, log_response
from app.utils.security import validate_idempotency_key
from app.routers.metrics import record_request, record_mcp_tool_execution


logger = get_logger(__name__)
router = APIRouter(prefix="/mcp", tags=["mcp"])


async def validate_mcp_idempotency(request: MCPToolRequest) -> None:
    """Validate idempotency key and check for existing request."""
    if not validate_idempotency_key(request.idempotency_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid idempotency key format"
        )
    
    # Check for existing request
    cached_response = await cache_manager.check_idempotency(request.idempotency_key)
    if cached_response:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request with this idempotency key already exists",
            headers={"X-Cached-Response": "true"}
        )


@router.post("/tools/execute", response_model=BaseResponse[MCPToolResponse])
async def execute_tool(
    request: MCPToolRequest,
    http_request: Request
) -> BaseResponse[MCPToolResponse]:
    """
    Execute a tool via MCP server.
    Idempotent operation - duplicate requests with same idempotency key are ignored.
    """
    start_time = time.time()
    
    # Log incoming request
    log_request(
        logger=logger,
        method=http_request.method,
        path=http_request.url.path,
        params=request.dict(),
        user_id=None  # Add user authentication here
    )
    
    try:
        # Validate idempotency
        await validate_mcp_idempotency(request)
        
        # Execute the tool
        tool_response = await mcp_service.execute_tool(request)
        
        # Store response in cache for idempotency
        await cache_manager.store_idempotency(
            request.idempotency_key,
            tool_response.dict()
        )
        
        # Record metrics
        record_mcp_tool_execution(request.tool_name, tool_response.success)
        
        response_time = time.time() - start_time
        log_response(logger, 200, response_time)
        record_request(http_request.method, http_request.url.path, 200, response_time)
        
        return BaseResponse(
            success=True,
            message="Tool executed successfully",
            data=tool_response
        )
    
    except HTTPException as e:
        response_time = time.time() - start_time
        log_response(logger, e.status_code, response_time, str(e.detail))
        record_request(http_request.method, http_request.url.path, e.status_code, response_time)
        record_mcp_tool_execution(request.tool_name, False)
        raise e
    
    except Exception as e:
        response_time = time.time() - start_time
        log_response(logger, 500, response_time, str(e))
        record_request(http_request.method, http_request.url.path, 500, response_time)
        record_mcp_tool_execution(request.tool_name, False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/agent/interact", response_model=BaseResponse[MCPAgentResponse])
async def interact_with_agent(
    request: MCPAgentRequest,
    http_request: Request
) -> BaseResponse[MCPAgentResponse]:
    """
    Interact with MCP agent.
    Idempotent operation - duplicate requests with same idempotency key are ignored.
    """
    start_time = time.time()
    
    # Log incoming request
    log_request(
        logger=logger,
        method=http_request.method,
        path=http_request.url.path,
        params=request.dict(),
        user_id=None  # Add user authentication here
    )
    
    try:
        # Validate idempotency
        if not validate_idempotency_key(request.idempotency_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid idempotency key format"
            )
        
        # Check for existing request
        cached_response = await cache_manager.check_idempotency(request.idempotency_key)
        if cached_response:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Request with this idempotency key already exists",
                headers={"X-Cached-Response": "true"}
            )
        
        # Interact with agent
        agent_response = await mcp_service.interact_with_agent(request)
        
        # Store response in cache for idempotency
        await cache_manager.store_idempotency(
            request.idempotency_key,
            agent_response.dict()
        )
        
        response_time = time.time() - start_time
        log_response(logger, 200, response_time)
        record_request(http_request.method, http_request.url.path, 200, response_time)
        
        return BaseResponse(
            success=True,
            message="Agent interaction completed successfully",
            data=agent_response
        )
    
    except HTTPException as e:
        response_time = time.time() - start_time
        log_response(logger, e.status_code, response_time, str(e.detail))
        record_request(http_request.method, http_request.url.path, e.status_code, response_time)
        raise e
    
    except Exception as e:
        response_time = time.time() - start_time
        log_response(logger, 500, response_time, str(e))
        record_request(http_request.method, http_request.url.path, 500, response_time)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
