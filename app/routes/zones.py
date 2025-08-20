import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.middleware import get_current_user
from app.models import Telemetry, Zone
from app.schemas import GeoJSONFeatureCollection, RouteResponse, RoutePoint, ZoneResponse

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/", response_model=GeoJSONFeatureCollection)
async def get_zones(
    session: AsyncSession = Depends(get_async_session),
    # current_user: dict = Depends(get_current_user),  # Temporarily disabled for testing
):
    """Get all zones as GeoJSON FeatureCollection."""
    try:
        stmt = select(Zone).order_by(Zone.name.asc())
        result = await session.execute(stmt)
        zones = result.scalars().all()
        
        features = []
        for zone in zones:
            try:
                # Convert WKBElement to GeoJSON using PostGIS ST_AsGeoJSON
                from sqlalchemy import text
                geom_result = await session.execute(
                    text("SELECT ST_AsGeoJSON(:geom) as geojson"),
                    {"geom": zone.geom}
                )
                geom_data = json.loads(geom_result.scalar())
                
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id": str(zone.id),
                        "name": zone.name,
                        "zone_type": zone.zone_type,
                        "max_dwell_minutes": zone.max_dwell_minutes,
                    },
                    "geometry": geom_data,
                }
                features.append(feature)
            except Exception as e:
                print(f"Error processing geometry for zone {zone.id}: {e}")
                continue
        
        return GeoJSONFeatureCollection(features=features)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve zones: {str(e)}",
        )


@router.get("/routes", response_model=RouteResponse)
async def get_routes(
    auv_id: str = Query(..., description="AUV identifier"),
    from_timestamp: datetime = Query(..., alias="from", description="Start timestamp"),
    to_timestamp: datetime = Query(..., alias="to", description="End timestamp"),
    session: AsyncSession = Depends(get_async_session),
    # current_user: dict = Depends(get_current_user),  # Temporarily disabled for testing
):
    """Get AUV route as a series of points."""
    try:
        # Get telemetry points for the route
        stmt = select(Telemetry).where(
            Telemetry.auv_id == auv_id,
            Telemetry.timestamp >= from_timestamp,
            Telemetry.timestamp <= to_timestamp,
        ).order_by(Telemetry.timestamp.asc())
        
        result = await session.execute(stmt)
        telemetry_points = result.scalars().all()
        
        # Convert to route points
        points = []
        for point in telemetry_points:
            route_point = RoutePoint(
                lat=point.position_lat,
                lng=point.position_lng,
                timestamp=point.timestamp,
            )
            points.append(route_point)
        
        return RouteResponse(
            auv_id=auv_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            points=points,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve route: {str(e)}",
        )


@router.get("/list", response_model=List[ZoneResponse])
async def list_zones(
    session: AsyncSession = Depends(get_async_session),
    # current_user: dict = Depends(get_current_user),  # Temporarily disabled for testing
):
    """Get list of all zones."""
    try:
        stmt = select(Zone).order_by(Zone.name.asc())
        result = await session.execute(stmt)
        zones = result.scalars().all()
        
        return [
            ZoneResponse(
                id=zone.id,
                name=zone.name,
                zone_type=zone.zone_type,
                geom=str(zone.geom),  # Convert WKBElement to string
                max_dwell_minutes=zone.max_dwell_minutes,
                created_at=zone.created_at,
                updated_at=zone.updated_at,
            )
            for zone in zones
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve zones: {str(e)}",
        )
