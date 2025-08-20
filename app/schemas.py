from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class Position(BaseModel):
    """Position data schema."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")
    depth: int = Field(..., ge=0, description="Depth in meters")
    speed: float = Field(..., ge=0, description="Speed in m/s")
    heading: int = Field(..., ge=0, le=360, description="Heading in degrees")


class Environment(BaseModel):
    """Environmental data schema."""
    turbidity_ntu: float = Field(..., ge=0, description="Turbidity in NTU")
    sediment_mg_l: float = Field(..., ge=0, description="Sediment concentration in mg/L")
    dissolved_oxygen_mg_l: float = Field(..., ge=0, description="Dissolved oxygen in mg/L")
    temperature_c: float = Field(..., description="Temperature in Celsius")


class Plume(BaseModel):
    """Plume data schema."""
    concentration_mg_l: float = Field(..., ge=0, description="Plume concentration in mg/L")


class SpeciesDetection(BaseModel):
    """Species detection schema."""
    name: str = Field(..., min_length=1, description="Species name")
    distance_m: float = Field(..., ge=0, description="Distance in meters")


class Battery(BaseModel):
    """Battery data schema."""
    level_pct: int = Field(..., ge=0, le=100, description="Battery level percentage")
    voltage_v: float = Field(..., ge=0, description="Battery voltage in volts")


class TelemetryCreate(BaseModel):
    """Telemetry ingestion schema."""
    timestamp: datetime = Field(..., description="Timestamp of the telemetry data")
    auv_id: str = Field(..., min_length=1, max_length=50, description="AUV identifier")
    position: Position
    env: Environment
    plume: Plume
    species_detections: List[SpeciesDetection] = Field(default_factory=list)
    battery: Battery


class TelemetryResponse(BaseModel):
    """Telemetry response schema."""
    id: UUID
    timestamp: datetime
    auv_id: str
    position: Position
    env: Environment
    plume: Plume
    battery: Battery
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRuleConfig(BaseModel):
    """Alert rule configuration schema."""
    id: str = Field(..., description="Rule identifier")
    type: str = Field(..., description="Rule type")
    path: str = Field(..., description="Data path to evaluate")
    operator: str = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value")
    severity: str = Field(..., pattern="^(low|medium|high)$", description="Alert severity")
    dedupe_window_sec: int = Field(..., ge=0, description="Deduplication window in seconds")
    zone_type: Optional[str] = Field(None, description="Zone type for zone-based rules")
    max_minutes: Optional[int] = Field(None, ge=0, description="Maximum dwell time in minutes")


class AlertRuleCreate(BaseModel):
    """Alert rule creation schema."""
    id: str = Field(..., min_length=1, max_length=50, description="Rule identifier")
    type: str = Field(..., description="Rule type")
    config: AlertRuleConfig
    active: bool = Field(default=True, description="Whether the rule is active")


class AlertRuleResponse(BaseModel):
    """Alert rule response schema."""
    id: str
    type: str
    config: AlertRuleConfig
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Alert response schema."""
    id: UUID
    created_at: datetime
    auv_id: str
    rule_id: str
    severity: str
    title: str
    message: str
    payload: Dict[str, Any]

    class Config:
        from_attributes = True


class AlertEvent(BaseModel):
    """Alert event for SSE streaming."""
    id: str
    timestamp: datetime
    auv_id: str
    severity: str
    title: str
    message: str


class TelemetryEvent(BaseModel):
    """Telemetry event for SSE streaming."""
    id: str
    timestamp: datetime
    auv_id: str
    position: Position
    env: Environment
    plume: Plume
    battery: Battery


class ZoneCreate(BaseModel):
    """Zone creation schema."""
    name: str = Field(..., min_length=1, max_length=200, description="Zone name")
    zone_type: str = Field(..., description="Zone type")
    geom: str = Field(..., description="GeoJSON geometry as string")
    max_dwell_minutes: int = Field(..., ge=0, description="Maximum dwell time in minutes")


class ZoneResponse(BaseModel):
    """Zone response schema."""
    id: UUID
    name: str
    zone_type: str
    geom: str
    max_dwell_minutes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GeoJSONFeature(BaseModel):
    """GeoJSON feature schema."""
    type: str = Field(default="Feature")
    properties: Dict[str, Any]
    geometry: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON feature collection schema."""
    type: str = Field(default="FeatureCollection")
    features: List[GeoJSONFeature]


class RoutePoint(BaseModel):
    """Route point schema."""
    lat: float
    lng: float
    timestamp: datetime


class RouteResponse(BaseModel):
    """Route response schema."""
    auv_id: str
    from_timestamp: datetime
    to_timestamp: datetime
    points: List[RoutePoint]


class ExportParams(BaseModel):
    """Export parameters schema."""
    from_timestamp: datetime = Field(..., alias="from", description="Start timestamp")
    to_timestamp: datetime = Field(..., alias="to", description="End timestamp")
    auv_id: Optional[str] = Field(None, description="AUV identifier filter")

    class Config:
        allow_population_by_field_name = True


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    database: str
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Metrics response schema."""
    timestamp: datetime
    streams: Dict[str, int]
    uptime: float
    memory: Dict[str, Any]
    version: str


class TelemetryIngestResponse(BaseModel):
    """Telemetry ingestion response schema."""
    success: bool
    telemetry_id: UUID
    alerts_generated: int
