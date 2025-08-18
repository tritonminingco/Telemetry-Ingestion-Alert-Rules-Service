import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from shapely.geometry import Point, Polygon
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, AlertRule, Zone
from app.schemas import AlertRuleConfig, TelemetryCreate


class RuleEvaluationResult:
    """Result of rule evaluation."""
    
    def __init__(self, triggered: bool, message: str = "", title: str = ""):
        self.triggered = triggered
        self.message = message
        self.title = title


class RuleEngine:
    """Alert rules engine."""
    
    @staticmethod
    def get_value_by_path(obj: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation path."""
        keys = path.split('.')
        current = obj
        
        for key in keys:
            if key.endswith('[]'):
                # Handle array access
                array_key = key[:-2]
                if array_key in current and isinstance(current[array_key], list):
                    return current[array_key]
                return []
            elif key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    @staticmethod
    def evaluate_threshold(
        telemetry: TelemetryCreate, rule_config: AlertRuleConfig
    ) -> RuleEvaluationResult:
        """Evaluate threshold-based rules."""
        value = RuleEngine.get_value_by_path(telemetry.dict(), rule_config.path)
        
        if value is None:
            return RuleEvaluationResult(False)
        
        triggered = False
        operator = rule_config.operator
        
        if operator == '>':
            triggered = value > rule_config.value
        elif operator == '<':
            triggered = value < rule_config.value
        elif operator == '>=':
            triggered = value >= rule_config.value
        elif operator == '<=':
            triggered = value <= rule_config.value
        elif operator == '==':
            triggered = value == rule_config.value
        elif operator == '!=':
            triggered = value != rule_config.value
        
        if triggered:
            message = (
                f"{rule_config.path} {operator} {rule_config.value} "
                f"(current: {value}) at {telemetry.position.lat:.4f},{telemetry.position.lng:.4f}"
            )
            title = f"{rule_config.path} threshold exceeded"
            return RuleEvaluationResult(True, message, title)
        
        return RuleEvaluationResult(False)
    
    @staticmethod
    def evaluate_proximity(
        telemetry: TelemetryCreate, rule_config: AlertRuleConfig
    ) -> RuleEvaluationResult:
        """Evaluate proximity-based rules for species detection."""
        species_detections = telemetry.species_detections
        
        if not species_detections:
            return RuleEvaluationResult(False)
        
        # Check if any species is closer than the threshold
        triggered_detections = [
            detection for detection in species_detections
            if detection.distance_m < rule_config.value
        ]
        
        if triggered_detections:
            # Find the closest species
            closest = min(triggered_detections, key=lambda x: x.distance_m)
            message = (
                f'Protected species "{closest.name}" detected at {closest.distance_m}m '
                f'(threshold: {rule_config.value}m) at {telemetry.position.lat:.4f},{telemetry.position.lng:.4f}'
            )
            title = "Protected species proximity alert"
            return RuleEvaluationResult(True, message, title)
        
        return RuleEvaluationResult(False)
    
    @staticmethod
    async def evaluate_zone_dwell(
        telemetry: TelemetryCreate, rule_config: AlertRuleConfig, session: AsyncSession
    ) -> RuleEvaluationResult:
        """Evaluate zone dwell time rules."""
        if not rule_config.zone_type:
            return RuleEvaluationResult(False)
        
        # Get zones of the specified type
        stmt = select(Zone).where(Zone.zone_type == rule_config.zone_type)
        result = await session.execute(stmt)
        zones = result.scalars().all()
        
        point = Point(telemetry.position.lng, telemetry.position.lat)
        
        for zone in zones:
            try:
                # Parse GeoJSON and create polygon
                geom_data = json.loads(zone.geom)
                if geom_data.get('type') == 'Polygon':
                    coordinates = geom_data['coordinates'][0]
                    polygon = Polygon(coordinates)
                    
                    if polygon.contains(point):
                        dwell_minutes = rule_config.max_minutes or 60
                        message = (
                            f"AUV in {zone.name} for more than {dwell_minutes} minutes "
                            f"at {telemetry.position.lat:.4f},{telemetry.position.lng:.4f}"
                        )
                        title = "Zone dwell time exceeded"
                        return RuleEvaluationResult(True, message, title)
            except Exception as e:
                print(f"Error evaluating zone dwell for zone {zone.id}: {e}")
                continue
        
        return RuleEvaluationResult(False)
    
    @staticmethod
    async def evaluate_rules(
        telemetry: TelemetryCreate, session: AsyncSession
    ) -> List[RuleEvaluationResult]:
        """Evaluate all active rules against telemetry data."""
        # Get all active rules
        stmt = select(AlertRule).where(AlertRule.active == True)
        result = await session.execute(stmt)
        rules = result.scalars().all()
        
        results = []
        
        for rule in rules:
            try:
                config = AlertRuleConfig(**rule.config)
                result = None
                
                if config.type in ['threshold', 'battery', 'dissolved_oxygen']:
                    result = RuleEngine.evaluate_threshold(telemetry, config)
                elif config.type == 'proximity':
                    result = RuleEngine.evaluate_proximity(telemetry, config)
                elif config.type == 'zone_dwell':
                    result = await RuleEngine.evaluate_zone_dwell(telemetry, config, session)
                else:
                    print(f"Unknown rule type: {config.type}")
                    continue
                
                if result.triggered:
                    results.append(result)
                    
            except Exception as e:
                print(f"Error evaluating rule {rule.id}: {e}")
                continue
        
        return results
    
    @staticmethod
    async def check_deduplication(
        auv_id: str, rule_id: str, dedupe_window_sec: int, session: AsyncSession
    ) -> bool:
        """Check if alert should be deduplicated."""
        window_start = datetime.utcnow() - timedelta(seconds=dedupe_window_sec)
        
        stmt = select(Alert).where(
            Alert.auv_id == auv_id,
            Alert.rule_id == rule_id,
            Alert.created_at >= window_start
        )
        
        result = await session.execute(stmt)
        existing_alert = result.scalar_one_or_none()
        
        return existing_alert is None  # Return True if no duplicate found
