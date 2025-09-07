# FastAPI HTTP Tools 主应用入口 - 应用初始化和配置
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import settings
from app.utils import setup_logging, get_logger, cache_manager
from app.routers import tools_email, tools_misc, meta, workflow
from app.routers.meta import record_request


# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Voice Agent Return Tools API", version=settings.app_version)
    
    try:
        # Connect to Redis for caching
        await cache_manager.connect()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        # Continue without Redis if connection fails
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voice Agent Return Tools API")
    await cache_manager.disconnect()
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI HTTP Tools for Voice Agent Return Processing",
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
    """Add request processing time to response headers and record metrics."""
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
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else None
        }
    )


# Include routers
app.include_router(tools_email.router)
app.include_router(tools_misc.router)
app.include_router(meta.router)
app.include_router(workflow.router)


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else None,
        "tools": [
            "POST /tools/make_rma_email",
            "POST /tools/send_email",
            "POST /tools/log_submission",
            "POST /tools/send_sms",
            "GET /health",
            "GET /metrics"
        ],
        "workflow": [
            "POST /workflow/return",
            "POST /workflow/policy",
            "GET /workflow/status"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
