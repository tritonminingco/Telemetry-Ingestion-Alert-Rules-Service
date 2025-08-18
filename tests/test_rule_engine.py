import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.rule_engine import RuleEngine, RuleEvaluationResult
from app.schemas import TelemetryCreate, Position, Environment, Plume, Battery, SpeciesDetection


@pytest.fixture
def sample_telemetry():
    """Sample telemetry data for testing."""
    return TelemetryCreate(
        timestamp=datetime.utcnow(),
        auv_id="AUV-003",
        position=Position(
            lat=-14.6572,
            lng=-125.4251,
            depth=3210,
            speed=1.2,
            heading=278,
        ),
        env=Environment(
            turbidity_ntu=8.7,
            sediment_mg_l=12.3,
            dissolved_oxygen_mg_l=6.8,
            temperature_c=4.3,
        ),
        plume=Plume(concentration_mg_l=52.0),
        species_detections=[
            SpeciesDetection(name="Benthic Octopod", distance_m=120)
        ],
        battery=Battery(level_pct=32, voltage_v=44.1),
    )


class TestRuleEngine:
    """Test cases for RuleEngine."""
    
    def test_get_value_by_path_simple(self):
        """Test getting value by simple path."""
        data = {"a": {"b": {"c": 123}}}
        result = RuleEngine.get_value_by_path(data, "a.b.c")
        assert result == 123
    
    def test_get_value_by_path_array(self):
        """Test getting value by path with array access."""
        data = {"items": [{"id": 1}, {"id": 2}]}
        result = RuleEngine.get_value_by_path(data, "items[].id")
        assert result == [{"id": 1}, {"id": 2}]
    
    def test_get_value_by_path_not_found(self):
        """Test getting value by path that doesn't exist."""
        data = {"a": {"b": 123}}
        result = RuleEngine.get_value_by_path(data, "a.b.c")
        assert result is None
    
    def test_evaluate_threshold_greater_than(self, sample_telemetry):
        """Test threshold evaluation with greater than operator."""
        from app.schemas import AlertRuleConfig
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="threshold",
            path="env.sediment_mg_l",
            operator=">",
            value=10.0,
            severity="high",
            dedupe_window_sec=300,
        )
        
        result = RuleEngine.evaluate_threshold(sample_telemetry, config)
        assert result.triggered is True
        assert "sediment_mg_l > 10.0" in result.message
    
    def test_evaluate_threshold_less_than(self, sample_telemetry):
        """Test threshold evaluation with less than operator."""
        from app.schemas import AlertRuleConfig
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="threshold",
            path="env.sediment_mg_l",
            operator="<",
            value=10.0,
            severity="high",
            dedupe_window_sec=300,
        )
        
        result = RuleEngine.evaluate_threshold(sample_telemetry, config)
        assert result.triggered is False
    
    def test_evaluate_threshold_battery_low(self, sample_telemetry):
        """Test battery threshold evaluation."""
        from app.schemas import AlertRuleConfig
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="threshold",
            path="battery.level_pct",
            operator="<",
            value=50,
            severity="medium",
            dedupe_window_sec=600,
        )
        
        result = RuleEngine.evaluate_threshold(sample_telemetry, config)
        assert result.triggered is True
        assert "battery.level_pct < 50" in result.message
    
    def test_evaluate_proximity_with_detection(self, sample_telemetry):
        """Test proximity evaluation with species detection."""
        from app.schemas import AlertRuleConfig
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="proximity",
            path="species_detections[].distance_m",
            operator="<",
            value=150,
            severity="high",
            dedupe_window_sec=600,
        )
        
        result = RuleEngine.evaluate_proximity(sample_telemetry, config)
        assert result.triggered is True
        assert "Protected species" in result.message
    
    def test_evaluate_proximity_no_detection(self, sample_telemetry):
        """Test proximity evaluation without species detection."""
        from app.schemas import AlertRuleConfig
        
        # Remove species detections
        sample_telemetry.species_detections = []
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="proximity",
            path="species_detections[].distance_m",
            operator="<",
            value=150,
            severity="high",
            dedupe_window_sec=600,
        )
        
        result = RuleEngine.evaluate_proximity(sample_telemetry, config)
        assert result.triggered is False
    
    def test_evaluate_proximity_distance_too_far(self, sample_telemetry):
        """Test proximity evaluation with distance too far."""
        from app.schemas import AlertRuleConfig
        
        # Set distance to be far
        sample_telemetry.species_detections[0].distance_m = 200
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="proximity",
            path="species_detections[].distance_m",
            operator="<",
            value=150,
            severity="high",
            dedupe_window_sec=600,
        )
        
        result = RuleEngine.evaluate_proximity(sample_telemetry, config)
        assert result.triggered is False
    
    @pytest.mark.asyncio
    async def test_evaluate_zone_dwell_in_zone(self, sample_telemetry):
        """Test zone dwell evaluation when AUV is in zone."""
        from app.schemas import AlertRuleConfig
        from app.models import Zone
        import json
        
        # Mock session
        mock_session = AsyncMock()
        
        # Mock zone
        mock_zone = MagicMock()
        mock_zone.id = "test-zone"
        mock_zone.name = "Test Zone"
        mock_zone.geom = json.dumps({
            "type": "Polygon",
            "coordinates": [[
                [-125.5, -14.7],
                [-125.3, -14.7],
                [-125.3, -14.6],
                [-125.5, -14.6],
                [-125.5, -14.7]
            ]]
        })
        
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_zone]
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="zone_dwell",
            path="position",
            operator="in",
            value=0,
            severity="medium",
            dedupe_window_sec=1800,
            zone_type="sensitive",
            max_minutes=60,
        )
        
        result = await RuleEngine.evaluate_zone_dwell(sample_telemetry, config, mock_session)
        assert result.triggered is True
        assert "Zone dwell time exceeded" in result.title
    
    @pytest.mark.asyncio
    async def test_evaluate_zone_dwell_not_in_zone(self, sample_telemetry):
        """Test zone dwell evaluation when AUV is not in zone."""
        from app.schemas import AlertRuleConfig
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = []
        
        config = AlertRuleConfig(
            id="TEST-RULE",
            type="zone_dwell",
            path="position",
            operator="in",
            value=0,
            severity="medium",
            dedupe_window_sec=1800,
            zone_type="sensitive",
            max_minutes=60,
        )
        
        result = await RuleEngine.evaluate_zone_dwell(sample_telemetry, config, mock_session)
        assert result.triggered is False
    
    @pytest.mark.asyncio
    async def test_check_deduplication_no_existing_alert(self):
        """Test deduplication check when no existing alert."""
        from datetime import datetime, timedelta
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await RuleEngine.check_deduplication(
            "AUV-003", "RULE-001", 300, mock_session
        )
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_deduplication_existing_alert(self):
        """Test deduplication check when existing alert found."""
        from datetime import datetime, timedelta
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = MagicMock()
        
        result = await RuleEngine.check_deduplication(
            "AUV-003", "RULE-001", 300, mock_session
        )
        assert result is False


class TestRuleEvaluationResult:
    """Test cases for RuleEvaluationResult."""
    
    def test_rule_evaluation_result_triggered(self):
        """Test RuleEvaluationResult when triggered."""
        result = RuleEvaluationResult(
            triggered=True,
            message="Test alert message",
            title="Test Alert"
        )
        
        assert result.triggered is True
        assert result.message == "Test alert message"
        assert result.title == "Test Alert"
    
    def test_rule_evaluation_result_not_triggered(self):
        """Test RuleEvaluationResult when not triggered."""
        result = RuleEvaluationResult(triggered=False)
        
        assert result.triggered is False
        assert result.message == ""
        assert result.title == ""
