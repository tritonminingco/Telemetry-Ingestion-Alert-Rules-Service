import asyncio
import json
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import Request
from sse_starlette import EventSourceResponse

from app.schemas import AlertEvent, TelemetryEvent


class StreamManager:
    """Manages Server-Sent Events streams."""
    
    def __init__(self):
        self.alert_streams: Dict[str, List[Request]] = {}
        self.telemetry_streams: Dict[str, List[Request]] = {}
        self._lock = asyncio.Lock()
    
    async def add_alert_stream(self, auv_id: Optional[str], request: Request) -> None:
        """Add a new alert stream."""
        async with self._lock:
            key = auv_id or "all"
            if key not in self.alert_streams:
                self.alert_streams[key] = []
            self.alert_streams[key].append(request)
    
    async def add_telemetry_stream(self, auv_id: Optional[str], request: Request) -> None:
        """Add a new telemetry stream."""
        async with self._lock:
            key = auv_id or "all"
            if key not in self.telemetry_streams:
                self.telemetry_streams[key] = []
            self.telemetry_streams[key].append(request)
    
    async def remove_alert_stream(self, auv_id: Optional[str], request: Request) -> None:
        """Remove an alert stream."""
        async with self._lock:
            key = auv_id or "all"
            if key in self.alert_streams:
                self.alert_streams[key] = [
                    req for req in self.alert_streams[key] if req != request
                ]
                if not self.alert_streams[key]:
                    del self.alert_streams[key]
    
    async def remove_telemetry_stream(self, auv_id: Optional[str], request: Request) -> None:
        """Remove a telemetry stream."""
        async with self._lock:
            key = auv_id or "all"
            if key in self.telemetry_streams:
                self.telemetry_streams[key] = [
                    req for req in self.telemetry_streams[key] if req != request
                ]
                if not self.telemetry_streams[key]:
                    del self.telemetry_streams[key]
    
    async def send_alert_event(self, event: AlertEvent, auv_id: Optional[str] = None) -> None:
        """Send alert event to all relevant streams."""
        event_data = {
            "id": str(event.id),
            "timestamp": event.timestamp.isoformat(),
            "auv_id": event.auv_id,
            "severity": event.severity,
            "title": event.title,
            "message": event.message,
        }
        
        # Send to specific AUV stream
        if auv_id:
            await self._send_to_alert_streams(auv_id, event_data)
        
        # Send to all streams
        await self._send_to_alert_streams("all", event_data)
    
    async def send_telemetry_event(self, event: TelemetryEvent, auv_id: Optional[str] = None) -> None:
        """Send telemetry event to all relevant streams."""
        event_data = {
            "id": str(event.id),
            "timestamp": event.timestamp.isoformat(),
            "auv_id": event.auv_id,
            "position": {
                "lat": event.position.lat,
                "lng": event.position.lng,
                "depth": event.position.depth,
                "speed": event.position.speed,
                "heading": event.position.heading,
            },
            "env": {
                "turbidity_ntu": event.env.turbidity_ntu,
                "sediment_mg_l": event.env.sediment_mg_l,
                "dissolved_oxygen_mg_l": event.env.dissolved_oxygen_mg_l,
                "temperature_c": event.env.temperature_c,
            },
            "plume": {
                "concentration_mg_l": event.plume.concentration_mg_l,
            },
            "battery": {
                "level_pct": event.battery.level_pct,
                "voltage_v": event.battery.voltage_v,
            },
        }
        
        # Send to specific AUV stream
        if auv_id:
            await self._send_to_telemetry_streams(auv_id, event_data)
        
        # Send to all streams
        await self._send_to_telemetry_streams("all", event_data)
    
    async def _send_to_alert_streams(self, key: str, event_data: dict) -> None:
        """Send event to alert streams for a specific key."""
        async with self._lock:
            if key not in self.alert_streams:
                return
            
            # Create a copy of the list to avoid modification during iteration
            streams = self.alert_streams[key].copy()
        
        # Send to all streams
        for request in streams:
            try:
                # Check if client is still connected
                if await request.is_disconnected():
                    await self.remove_alert_stream(key, request)
                    continue
                
                # Send the event
                await request.send_json(event_data)
            except Exception as e:
                print(f"Error sending alert event: {e}")
                await self.remove_alert_stream(key, request)
    
    async def _send_to_telemetry_streams(self, key: str, event_data: dict) -> None:
        """Send event to telemetry streams for a specific key."""
        async with self._lock:
            if key not in self.telemetry_streams:
                return
            
            # Create a copy of the list to avoid modification during iteration
            streams = self.telemetry_streams[key].copy()
        
        # Send to all streams
        for request in streams:
            try:
                # Check if client is still connected
                if await request.is_disconnected():
                    await self.remove_telemetry_stream(key, request)
                    continue
                
                # Send the event
                await request.send_json(event_data)
            except Exception as e:
                print(f"Error sending telemetry event: {e}")
                await self.remove_telemetry_stream(key, request)
    
    def get_active_streams(self) -> Dict[str, int]:
        """Get count of active streams."""
        async with self._lock:
            return {
                "alert_streams": sum(len(streams) for streams in self.alert_streams.values()),
                "telemetry_streams": sum(len(streams) for streams in self.telemetry_streams.values()),
            }
    
    async def close_all_streams(self) -> None:
        """Close all active streams."""
        async with self._lock:
            self.alert_streams.clear()
            self.telemetry_streams.clear()


# Global stream manager instance
stream_manager = StreamManager()


async def alert_stream_generator(auv_id: Optional[str] = None):
    """Generate alert stream events."""
    request = None
    
    try:
        # Send initial connection event
        connection_event = AlertEvent(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            auv_id="system",
            severity="low",
            title="Connected",
            message="Alert stream connected",
        )
        
        yield {
            "event": "connect",
            "data": connection_event.json(),
        }
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield {
                "event": "ping",
                "data": "keepalive",
            }
            
    except asyncio.CancelledError:
        if request:
            await stream_manager.remove_alert_stream(auv_id, request)


async def telemetry_stream_generator(auv_id: Optional[str] = None):
    """Generate telemetry stream events."""
    request = None
    
    try:
        # Send initial connection event
        connection_event = TelemetryEvent(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            auv_id="system",
            position=Position(lat=0, lng=0, depth=0, speed=0, heading=0),
            env=Environment(turbidity_ntu=0, sediment_mg_l=0, dissolved_oxygen_mg_l=0, temperature_c=0),
            plume=Plume(concentration_mg_l=0),
            battery=Battery(level_pct=0, voltage_v=0),
        )
        
        yield {
            "event": "connect",
            "data": connection_event.json(),
        }
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield {
                "event": "ping",
                "data": "keepalive",
            }
            
    except asyncio.CancelledError:
        if request:
            await stream_manager.remove_telemetry_stream(auv_id, request)
