from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from geoalchemy2 import Geometry
    HAS_POSTGIS = True
except ImportError:
    HAS_POSTGIS = False

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Telemetry(Base):
    """Telemetry data model."""
    
    __tablename__ = "telemetry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    auv_id = Column(String(50), nullable=False, index=True)
    
    # Position data
    position_lat = Column(Float, nullable=False)
    position_lng = Column(Float, nullable=False)
    depth_m = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    heading = Column(Integer, nullable=False)
    
    # Environmental data
    sediment_mg_l = Column(Float, nullable=False)
    turbidity_ntu = Column(Float, nullable=False)
    dissolved_oxygen_mg_l = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=False)
    
    # Plume data
    plume_concentration_mg_l = Column(Float, nullable=False)
    
    # Battery data
    battery_pct = Column(Integer, nullable=False)
    
    # Raw data
    raw = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    alerts = relationship("Alert", back_populates="telemetry")
    
    # Indexes
    __table_args__ = (
        Index("idx_telemetry_timestamp_auv", "timestamp", "auv_id"),
        Index("idx_telemetry_auv_timestamp", "auv_id", "timestamp"),
    )


class AlertRule(Base):
    """Alert rule configuration model."""
    
    __tablename__ = "alert_rules"
    
    id = Column(String(50), primary_key=True)
    type = Column(String(50), nullable=False)
    config = Column(JSONB, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = relationship("Alert", back_populates="rule")


class Alert(Base):
    """Alert model."""
    
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    auv_id = Column(String(50), nullable=False, index=True)
    rule_id = Column(String(50), ForeignKey("alert_rules.id"), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=False)
    
    # Optional link to telemetry record
    telemetry_id = Column(UUID(as_uuid=True), ForeignKey("telemetry.id"), nullable=True)
    
    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")
    telemetry = relationship("Telemetry", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index("idx_alerts_created_at_auv", "created_at", "auv_id"),
        Index("idx_alerts_auv_created_at", "auv_id", "created_at"),
    )


class Zone(Base):
    """Geographic zone model."""
    
    __tablename__ = "zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    zone_type = Column(String(50), nullable=False)
    geom = Column(Geometry("POLYGON", srid=4326), nullable=False) if HAS_POSTGIS else Column(Text, nullable=False)
    max_dwell_minutes = Column(Integer, nullable=False, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_zones_zone_type", "zone_type"),
    )
