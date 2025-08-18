import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.routes.zones import get_zones, get_routes, list_zones


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_zones():
    """Mock zone data."""
    return [
        {
            "id": "zone-1",
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
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        },
        {
            "id": "zone-2",
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
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    ]


@pytest.fixture
def mock_telemetry_points():
    """Mock telemetry points for routes."""
    points = []
    base_time = datetime.utcnow()
    
    for i in range(5):
        point = MagicMock()
        point.position_lat = -14.6572 + i * 0.001
        point.position_lng = -125.4251 + i * 0.001
        point.timestamp = base_time + timedelta(minutes=i * 10)
        points.append(point)
    
    return points


class TestZones:
    """Test cases for zones functionality."""
    
    @pytest.mark.asyncio
    async def test_get_zones_success(self, mock_session, mock_zones):
        """Test successful retrieval of zones as GeoJSON."""
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        for zone_data in mock_zones:
            mock_zone = MagicMock()
            mock_zone.id = zone_data["id"]
            mock_zone.name = zone_data["name"]
            mock_zone.zone_type = zone_data["zone_type"]
            mock_zone.geom = zone_data["geom"]
            mock_zone.max_dwell_minutes = zone_data["max_dwell_minutes"]
            mock_result.scalars.return_value.all.return_value.append(mock_zone)
        
        mock_session.execute.return_value = mock_result
        
        # Call the function
        response = await get_zones(
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify response structure
        assert response.type == "FeatureCollection"
        assert len(response.features) == 2
        
        # Check first feature
        feature = response.features[0]
        assert feature.type == "Feature"
        assert feature.properties["name"] == "CCZ Sensitive Area A"
        assert feature.properties["zone_type"] == "sensitive"
        assert feature.properties["max_dwell_minutes"] == 60
        
        # Check geometry
        geom = json.loads(feature.geometry)
        assert geom["type"] == "Polygon"
        assert len(geom["coordinates"][0]) == 5  # 5 points for polygon
    
    @pytest.mark.asyncio
    async def test_get_zones_empty(self, mock_session):
        """Test zones endpoint with no zones."""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        response = await get_zones(
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        assert response.type == "FeatureCollection"
        assert len(response.features) == 0
    
    @pytest.mark.asyncio
    async def test_get_zones_invalid_geometry(self, mock_session):
        """Test zones endpoint with invalid geometry."""
        # Mock zone with invalid geometry
        mock_zone = MagicMock()
        mock_zone.id = "zone-1"
        mock_zone.name = "Test Zone"
        mock_zone.zone_type = "sensitive"
        mock_zone.geom = "invalid json"
        mock_zone.max_dwell_minutes = 60
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_zone]
        mock_session.execute.return_value = mock_result
        
        # Should handle invalid geometry gracefully
        response = await get_zones(
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        assert response.type == "FeatureCollection"
        assert len(response.features) == 0  # Invalid geometry should be skipped
    
    @pytest.mark.asyncio
    async def test_list_zones_success(self, mock_session, mock_zones):
        """Test successful retrieval of zones list."""
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        for zone_data in mock_zones:
            mock_zone = MagicMock()
            mock_zone.id = zone_data["id"]
            mock_zone.name = zone_data["name"]
            mock_zone.zone_type = zone_data["zone_type"]
            mock_zone.geom = zone_data["geom"]
            mock_zone.max_dwell_minutes = zone_data["max_dwell_minutes"]
            mock_zone.created_at = zone_data["created_at"]
            mock_zone.updated_at = zone_data["updated_at"]
            mock_result.scalars.return_value.all.return_value.append(mock_zone)
        
        mock_session.execute.return_value = mock_result
        
        # Call the function
        response = await list_zones(
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify response
        assert len(response) == 2
        
        # Check first zone
        zone = response[0]
        assert zone.name == "CCZ Sensitive Area A"
        assert zone.zone_type == "sensitive"
        assert zone.max_dwell_minutes == 60
        assert zone.geom == mock_zones[0]["geom"]


class TestRoutes:
    """Test cases for routes functionality."""
    
    @pytest.mark.asyncio
    async def test_get_routes_success(self, mock_session, mock_telemetry_points):
        """Test successful retrieval of AUV route."""
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_telemetry_points
        mock_session.execute.return_value = mock_result
        
        # Test parameters
        auv_id = "AUV-001"
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        
        # Call the function
        response = await get_routes(
            auv_id=auv_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify response
        assert response.auv_id == auv_id
        assert response.from_timestamp == from_timestamp
        assert response.to_timestamp == to_timestamp
        assert len(response.points) == 5
        
        # Check first point
        point = response.points[0]
        assert point.lat == -14.6572
        assert point.lng == -125.4251
        assert isinstance(point.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_get_routes_empty(self, mock_session):
        """Test routes endpoint with no telemetry points."""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        auv_id = "AUV-001"
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        
        response = await get_routes(
            auv_id=auv_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        assert response.auv_id == auv_id
        assert len(response.points) == 0
    
    @pytest.mark.asyncio
    async def test_get_routes_ordered_by_timestamp(self, mock_session, mock_telemetry_points):
        """Test that route points are ordered by timestamp."""
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_telemetry_points
        mock_session.execute.return_value = mock_result
        
        auv_id = "AUV-001"
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        
        response = await get_routes(
            auv_id=auv_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify points are ordered by timestamp
        for i in range(len(response.points) - 1):
            assert response.points[i].timestamp <= response.points[i + 1].timestamp
    
    @pytest.mark.asyncio
    async def test_get_routes_coordinate_precision(self, mock_session):
        """Test coordinate precision in route points."""
        # Create telemetry points with specific coordinates
        mock_point = MagicMock()
        mock_point.position_lat = -14.657234
        mock_point.position_lng = -125.425167
        mock_point.timestamp = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_point]
        mock_session.execute.return_value = mock_result
        
        auv_id = "AUV-001"
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        
        response = await get_routes(
            auv_id=auv_id,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify coordinate precision is preserved
        point = response.points[0]
        assert point.lat == -14.657234
        assert point.lng == -125.425167
