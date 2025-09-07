# 测试配置和夹具 - 提供测试环境的基础配置和共享夹具
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from app.utils.cache import cache_manager


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for synchronous testing."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_test_cache():
    """Setup test cache environment."""
    # Mock Redis connection for tests
    cache_manager.redis = None
    yield
    # Cleanup after tests
    cache_manager.redis = None


@pytest.fixture
def sample_vapi_call_request():
    """Sample Vapi call request for testing."""
    return {
        "idempotency_key": "test-key-123",
        "phone_number": "1234567890",
        "assistant_id": "assistant-123",
        "customer_id": "customer-123",
        "metadata": {"test": True}
    }


@pytest.fixture
def sample_mcp_tool_request():
    """Sample MCP tool request for testing."""
    return {
        "idempotency_key": "test-mcp-key-123",
        "tool_name": "test_tool",
        "parameters": {"param1": "value1"},
        "context": {"test": True}
    }


@pytest.fixture
def sample_mcp_agent_request():
    """Sample MCP agent request for testing."""
    return {
        "idempotency_key": "test-agent-key-123",
        "message": "Hello, test message",
        "session_id": "session-123",
        "context": {"test": True}
    }
