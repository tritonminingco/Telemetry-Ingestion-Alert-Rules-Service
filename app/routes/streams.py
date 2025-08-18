from typing import Optional

from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

from app.stream_manager import stream_manager

router = APIRouter(prefix="/stream", tags=["streams"])


@router.get("/alerts")
async def stream_alerts(
    request: Request,
    auv_id: Optional[str] = None,
):
    """Stream alert events via Server-Sent Events."""
    
    async def event_generator():
        try:
            # Add this stream to the manager
            await stream_manager.add_alert_stream(auv_id, request)
            
            # Send initial connection event
            yield {
                "event": "connect",
                "data": {
                    "id": "connection",
                    "timestamp": datetime.utcnow().isoformat(),
                    "auv_id": "system",
                    "severity": "low",
                    "title": "Connected",
                    "message": "Alert stream connected",
                },
            }
            
            # Keep connection alive
            while True:
                if await request.is_disconnected():
                    break
                
                await asyncio.sleep(30)
                yield {
                    "event": "ping",
                    "data": "keepalive",
                }
                
        except asyncio.CancelledError:
            pass
        finally:
            # Remove stream when disconnected
            await stream_manager.remove_alert_stream(auv_id, request)
    
    return EventSourceResponse(event_generator())


@router.get("/telemetry")
async def stream_telemetry(
    request: Request,
    auv_id: Optional[str] = None,
):
    """Stream telemetry events via Server-Sent Events."""
    
    async def event_generator():
        try:
            # Add this stream to the manager
            await stream_manager.add_telemetry_stream(auv_id, request)
            
            # Send initial connection event
            yield {
                "event": "connect",
                "data": {
                    "id": "connection",
                    "timestamp": datetime.utcnow().isoformat(),
                    "auv_id": "system",
                    "position": {"lat": 0, "lng": 0, "depth": 0, "speed": 0, "heading": 0},
                    "env": {"turbidity_ntu": 0, "sediment_mg_l": 0, "dissolved_oxygen_mg_l": 0, "temperature_c": 0},
                    "plume": {"concentration_mg_l": 0},
                    "battery": {"level_pct": 0, "voltage_v": 0},
                },
            }
            
            # Keep connection alive
            while True:
                if await request.is_disconnected():
                    break
                
                await asyncio.sleep(30)
                yield {
                    "event": "ping",
                    "data": "keepalive",
                }
                
        except asyncio.CancelledError:
            pass
        finally:
            # Remove stream when disconnected
            await stream_manager.remove_telemetry_stream(auv_id, request)
    
    return EventSourceResponse(event_generator())
