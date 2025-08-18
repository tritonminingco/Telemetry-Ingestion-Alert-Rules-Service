import psutil
from datetime import datetime

from fastapi import APIRouter, Depends, status

from app.database import check_db_health
from app.middleware import get_current_user
from app.schemas import HealthResponse, MetricsResponse
from app.stream_manager import stream_manager

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        db_healthy = await check_db_health()
        
        if not db_healthy:
            return HealthResponse(
                status="unhealthy",
                database="down",
                timestamp=datetime.utcnow(),
            )
        
        return HealthResponse(
            status="healthy",
            database="up",
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database="error",
            timestamp=datetime.utcnow(),
        )


@router.get("/readyz", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint."""
    try:
        db_healthy = await check_db_health()
        
        if not db_healthy:
            return HealthResponse(
                status="not ready",
                database="down",
                timestamp=datetime.utcnow(),
            )
        
        return HealthResponse(
            status="ready",
            database="up",
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        return HealthResponse(
            status="not ready",
            database="error",
            timestamp=datetime.utcnow(),
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get application metrics."""
    try:
        # Get stream metrics
        streams = stream_manager.get_active_streams()
        
        # Get system metrics
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free,
        }
        
        return MetricsResponse(
            timestamp=datetime.utcnow(),
            streams=streams,
            uptime=psutil.boot_time(),
            memory=memory_info,
            version="1.0.0",
        )
        
    except Exception as e:
        return MetricsResponse(
            timestamp=datetime.utcnow(),
            streams={"alert_streams": 0, "telemetry_streams": 0},
            uptime=0,
            memory={},
            version="1.0.0",
        )
