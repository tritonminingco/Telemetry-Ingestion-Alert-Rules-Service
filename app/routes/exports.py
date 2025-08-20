import csv
import io
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.middleware import get_current_user
from app.models import Alert, Telemetry

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/isa/hourly")
async def export_isa_hourly(
    from_timestamp: datetime = Query(..., alias="from", description="Start timestamp"),
    to_timestamp: datetime = Query(..., alias="to", description="End timestamp"),
    auv_id: str = Query(None, description="AUV identifier filter"),
    session: AsyncSession = Depends(get_async_session),
    # current_user: dict = Depends(get_current_user),  # Temporarily disabled for testing
):
    """Export ISA hourly data as CSV."""
    try:
        # Build query conditions
        conditions = [
            Telemetry.timestamp >= from_timestamp,
            Telemetry.timestamp <= to_timestamp,
        ]
        
        if auv_id:
            conditions.append(Telemetry.auv_id == auv_id)
        
        # Get telemetry data with alert counts
        stmt = select(
            Telemetry,
            func.count(Alert.id).label("alerts_count")
        ).outerjoin(
            Alert, Telemetry.id == Alert.telemetry_id
        ).where(
            *conditions
        ).group_by(
            Telemetry.id
        ).order_by(
            Telemetry.timestamp.asc()
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        
        # Generate CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            "timestamp",
            "auv_id",
            "lat",
            "lng",
            "depth_m",
            "sediment_mg_l",
            "turbidity_ntu",
            "dissolved_oxygen_mg_l",
            "temperature_c",
            "plume_concentration_mg_l",
            "battery_pct",
            "alerts_count",
        ]
        writer.writerow(headers)
        
        # Write data rows
        for row in rows:
            telemetry = row[0]
            alerts_count = row[1]
            
            csv_row = [
                telemetry.timestamp.isoformat(),
                telemetry.auv_id,
                f"{telemetry.position_lat:.6f}",
                f"{telemetry.position_lng:.6f}",
                telemetry.depth_m,
                f"{telemetry.sediment_mg_l:.2f}",
                f"{telemetry.turbidity_ntu:.2f}",
                f"{telemetry.dissolved_oxygen_mg_l:.2f}",
                f"{telemetry.temperature_c:.2f}",
                f"{telemetry.plume_concentration_mg_l:.2f}",
                telemetry.battery_pct,
                alerts_count,
            ]
            writer.writerow(csv_row)
        
        # Prepare response
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename
        filename = f"isa_export_{from_timestamp.strftime('%Y%m%d')}_{to_timestamp.strftime('%Y%m%d')}.csv"
        if auv_id:
            filename = f"isa_export_{auv_id}_{from_timestamp.strftime('%Y%m%d')}_{to_timestamp.strftime('%Y%m%d')}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache",
            },
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate export: {str(e)}",
        )
