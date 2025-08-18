import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.database import init_db, init_timescaledb
from app.middleware import auth_middleware, rate_limit_middleware
from app.routes import telemetry, streams, exports, zones, health
from app.stream_manager import stream_manager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting DSG Telemetry Service")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize TimescaleDB (if available)
        await init_timescaledb()
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down DSG Telemetry Service")
    
    try:
        # Close all streams
        await stream_manager.close_all_streams()
        logger.info("All streams closed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AUV Telemetry Ingestion + Alert Rules Service",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"],
)

# Add custom middleware
@app.middleware("http")
async def auth_middleware_wrapper(request: Request, call_next):
    """Apply authentication middleware."""
    if request.url.path.startswith("/api/telemetry"):
        await auth_middleware(request)
    return await call_next(request)


@app.middleware("http")
async def rate_limit_middleware_wrapper(request: Request, call_next):
    """Apply rate limiting middleware."""
    await rate_limit_middleware(request)
    return await call_next(request)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(telemetry.router, prefix="/api")
app.include_router(streams.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(zones.router, prefix="/api")
app.include_router(health.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else None,
    }


@app.get("/openapi.json")
async def get_openapi():
    """Get OpenAPI specification."""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
