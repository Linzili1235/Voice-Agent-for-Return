# Vapi Agent API 主应用入口 - FastAPI 应用初始化和配置
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config.settings import settings
from app.utils.logging import setup_logging, get_logger
from app.utils.cache import cache_manager
from app.routers import health, metrics, vapi, mcp
from app.routers.metrics import record_request


# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Vapi Agent API", version=settings.app_version)
    
    try:
        # Connect to Redis
        await cache_manager.connect()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Vapi Agent API")
    await cache_manager.disconnect()
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A FastAPI backend for Vapi Agent with MCP integration",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record metrics
    record_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=process_time
    )
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(vapi.router)
app.include_router(mcp.router)


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else None
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
