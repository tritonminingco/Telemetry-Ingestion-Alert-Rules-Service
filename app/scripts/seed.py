import asyncio
import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import AlertRule, Zone


async def seed_data():
    """Seed initial data for the application."""
    
    async with AsyncSessionLocal() as session:
        # Seed alert rules
        alert_rules = [
            {
                "id": "RULE-SEDIMENT-01",
                "type": "threshold",
                "config": {
                    "id": "RULE-SEDIMENT-01",
                    "type": "threshold",
                    "path": "env.sediment_mg_l",
                    "operator": ">",
                    "value": 25,
                    "severity": "high",
                    "dedupe_window_sec": 300,
                },
                "active": True,
            },
            {
                "id": "RULE-DO-01",
                "type": "threshold",
                "config": {
                    "id": "RULE-DO-01",
                    "type": "threshold",
                    "path": "env.dissolved_oxygen_mg_l",
                    "operator": "<",
                    "value": 6.0,
                    "severity": "medium",
                    "dedupe_window_sec": 300,
                },
                "active": True,
            },
            {
                "id": "RULE-BATT-01",
                "type": "threshold",
                "config": {
                    "id": "RULE-BATT-01",
                    "type": "threshold",
                    "path": "battery.level_pct",
                    "operator": "<",
                    "value": 30,
                    "severity": "medium",
                    "dedupe_window_sec": 600,
                },
                "active": True,
            },
            {
                "id": "RULE-SPECIES-01",
                "type": "proximity",
                "config": {
                    "id": "RULE-SPECIES-01",
                    "type": "proximity",
                    "path": "species_detections[].distance_m",
                    "operator": "<",
                    "value": 150,
                    "severity": "high",
                    "dedupe_window_sec": 600,
                },
                "active": True,
            },
            {
                "id": "RULE-ZONE-01",
                "type": "zone_dwell",
                "config": {
                    "id": "RULE-ZONE-01",
                    "type": "zone_dwell",
                    "path": "position",
                    "operator": "in",
                    "value": 0,
                    "severity": "medium",
                    "dedupe_window_sec": 1800,
                    "zone_type": "sensitive",
                    "max_minutes": 60,
                },
                "active": True,
            },
        ]
        
        for rule_data in alert_rules:
            rule = AlertRule(**rule_data)
            session.add(rule)
        
        # Seed zones
        zones = [
            {
                "id": uuid4(),
                "name": "CCZ Sensitive Area A",
                "zone_type": "sensitive",
                "geom": json.dumps({
                    "type": "Polygon",
                    "coordinates": [[
                        [-140.0, 10.0],
                        [-139.0, 10.0],
                        [-139.0, 11.0],
                        [-140.0, 11.0],
                        [-140.0, 10.0]
                    ]]
                }),
                "max_dwell_minutes": 60,
            },
            {
                "id": uuid4(),
                "name": "Restricted No-Go",
                "zone_type": "restricted",
                "geom": json.dumps({
                    "type": "Polygon",
                    "coordinates": [[
                        [-145.0, 8.0],
                        [-144.0, 8.0],
                        [-144.0, 9.0],
                        [-145.0, 9.0],
                        [-145.0, 8.0]
                    ]]
                }),
                "max_dwell_minutes": 0,
            },
        ]
        
        for zone_data in zones:
            zone = Zone(**zone_data)
            session.add(zone)
        
        await session.commit()
        print("✅ Seed data created successfully")


if __name__ == "__main__":
    asyncio.run(seed_data())
