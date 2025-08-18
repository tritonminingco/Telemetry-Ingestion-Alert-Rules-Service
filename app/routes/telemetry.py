from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.middleware import get_current_user
from app.models import Alert, AlertRule, Telemetry
from app.rule_engine import RuleEngine
from app.schemas import (
    TelemetryCreate,
    TelemetryIngestResponse,
    TelemetryResponse,
    AlertEvent,
    TelemetryEvent,
)
from app.stream_manager import stream_manager

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post(
    "/ingest",
    response_model=TelemetryIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_telemetry(
    telemetry_data: TelemetryCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
):
    """Ingest telemetry data and evaluate alert rules."""
    try:
        # Create telemetry record
        telemetry_record = Telemetry(
            timestamp=telemetry_data.timestamp,
            auv_id=telemetry_data.auv_id,
            position_lat=telemetry_data.position.lat,
            position_lng=telemetry_data.position.lng,
            depth_m=telemetry_data.position.depth,
            speed=telemetry_data.position.speed,
            heading=telemetry_data.position.heading,
            sediment_mg_l=telemetry_data.env.sediment_mg_l,
            turbidity_ntu=telemetry_data.env.turbidity_ntu,
            dissolved_oxygen_mg_l=telemetry_data.env.dissolved_oxygen_mg_l,
            temperature_c=telemetry_data.env.temperature_c,
            plume_concentration_mg_l=telemetry_data.plume.concentration_mg_l,
            battery_pct=telemetry_data.battery.level_pct,
            raw=telemetry_data.dict(),
        )
        
        session.add(telemetry_record)
        await session.flush()  # Get the ID
        
        # Evaluate alert rules
        rule_results = await RuleEngine.evaluate_rules(telemetry_data, session)
        alerts_generated = 0
        
        for result in rule_results:
            # Get the rule that triggered this result
            stmt = select(AlertRule).where(AlertRule.active == True)
            rules = await session.execute(stmt)
            
            for rule in rules.scalars():
                config = rule.config
                if config.get("dedupe_window_sec"):
                    # Check deduplication
                    can_create = await RuleEngine.check_deduplication(
                        telemetry_data.auv_id,
                        rule.id,
                        config["dedupe_window_sec"],
                        session,
                    )
                    
                    if can_create:
                        # Create alert
                        alert = Alert(
                            auv_id=telemetry_data.auv_id,
                            rule_id=rule.id,
                            severity=config.get("severity", "medium"),
                            title=result.title,
                            message=result.message,
                            payload=telemetry_data.dict(),
                            telemetry_id=telemetry_record.id,
                        )
                        
                        session.add(alert)
                        alerts_generated += 1
                        
                        # Send alert event to stream
                        alert_event = AlertEvent(
                            id=str(alert.id),
                            timestamp=datetime.utcnow(),
                            auv_id=alert.auv_id,
                            severity=alert.severity,
                            title=alert.title,
                            message=alert.message,
                        )
                        
                        await stream_manager.send_alert_event(alert_event, telemetry_data.auv_id)
        
        await session.commit()
        
        # Send telemetry event to stream
        telemetry_event = TelemetryEvent(
            id=str(telemetry_record.id),
            timestamp=telemetry_record.timestamp,
            auv_id=telemetry_record.auv_id,
            position=telemetry_data.position,
            env=telemetry_data.env,
            plume=telemetry_data.plume,
            battery=telemetry_data.battery,
        )
        
        await stream_manager.send_telemetry_event(telemetry_event, telemetry_data.auv_id)
        
        return TelemetryIngestResponse(
            success=True,
            telemetry_id=telemetry_record.id,
            alerts_generated=alerts_generated,
        )
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest telemetry: {str(e)}",
        )


@router.get("/", response_model=List[TelemetryResponse])
async def get_telemetry(
    auv_id: str = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
):
    """Get telemetry data with optional filtering."""
    try:
        stmt = select(Telemetry)
        
        if auv_id:
            stmt = stmt.where(Telemetry.auv_id == auv_id)
        
        stmt = stmt.order_by(Telemetry.timestamp.desc()).limit(limit).offset(offset)
        
        result = await session.execute(stmt)
        telemetry_records = result.scalars().all()
        
        return [
            TelemetryResponse(
                id=record.id,
                timestamp=record.timestamp,
                auv_id=record.auv_id,
                position=telemetry_data.position,
                env=telemetry_data.env,
                plume=telemetry_data.plume,
                battery=telemetry_data.battery,
                created_at=record.created_at,
            )
            for record in telemetry_records
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve telemetry: {str(e)}",
        )
