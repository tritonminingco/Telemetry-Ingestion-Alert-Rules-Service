import pytest
import psutil
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.routes.health import health_check, readiness_check, get_metrics


@pytest.fixture
def mock_db_healthy():
    """Mock healthy database."""
    return True


@pytest.fixture
def mock_db_unhealthy():
    """Mock unhealthy database."""
    return False


class TestHealthChecks:
    """Test cases for health check endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.routes.health.check_db_health')
    async def test_health_check_healthy(self, mock_check_db, mock_db_healthy):
        """Test health check when database is healthy."""
        mock_check_db.return_value = True
        
        response = await health_check()
        
        assert response.status == "healthy"
        assert response.database == "up"
        assert isinstance(response.timestamp, datetime)
    
    @pytest.mark.asyncio
    @patch('app.routes.health.check_db_health')
    async def test_health_check_unhealthy(self, mock_check_db, mock_db_unhealthy):
        """Test health check when database is unhealthy."""
        mock_check_db.return_value = False
        
        response = await health_check()
        
        assert response.status == "unhealthy"
        assert response.database == "down"
        assert isinstance(response.timestamp, datetime)
    
    @pytest.mark.asyncio
    @patch('app.routes.health.check_db_health')
    async def test_health_check_exception(self, mock_check_db):
        """Test health check when database check raises exception."""
        mock_check_db.side_effect = Exception("Database connection failed")
        
        response = await health_check()
        
        assert response.status == "unhealthy"
        assert response.database == "error"
        assert isinstance(response.timestamp, datetime)
    
    @pytest.mark.asyncio
    @patch('app.routes.health.check_db_health')
    async def test_readiness_check_ready(self, mock_check_db, mock_db_healthy):
        """Test readiness check when service is ready."""
        mock_check_db.return_value = True
        
        response = await readiness_check()
        
        assert response.status == "ready"
        assert response.database == "up"
        assert isinstance(response.timestamp, datetime)
    
    @pytest.mark.asyncio
    @patch('app.routes.health.check_db_health')
    async def test_readiness_check_not_ready(self, mock_check_db, mock_db_unhealthy):
        """Test readiness check when service is not ready."""
        mock_check_db.return_value = False
        
        response = await readiness_check()
        
        assert response.status == "not ready"
        assert response.database == "down"
        assert isinstance(response.timestamp, datetime)
    
    @pytest.mark.asyncio
    @patch('app.routes.health.check_db_health')
    async def test_readiness_check_exception(self, mock_check_db):
        """Test readiness check when database check raises exception."""
        mock_check_db.side_effect = Exception("Database connection failed")
        
        response = await readiness_check()
        
        assert response.status == "not ready"
        assert response.database == "error"
        assert isinstance(response.timestamp, datetime)


class TestMetrics:
    """Test cases for metrics endpoint."""
    
    @pytest.mark.asyncio
    @patch('app.routes.health.stream_manager')
    @patch('app.routes.health.psutil.virtual_memory')
    @patch('app.routes.health.psutil.boot_time')
    async def test_get_metrics_success(self, mock_boot_time, mock_virtual_memory, mock_stream_manager):
        """Test successful metrics retrieval."""
        # Mock stream manager
        mock_stream_manager.get_active_streams.return_value = {
            "alert_streams": 5,
            "telemetry_streams": 3
        }
        
        # Mock memory info
        mock_memory = MagicMock()
        mock_memory.total = 8589934592  # 8GB
        mock_memory.available = 4294967296  # 4GB
        mock_memory.percent = 50.0
        mock_memory.used = 4294967296  # 4GB
        mock_memory.free = 4294967296  # 4GB
        mock_virtual_memory.return_value = mock_memory
        
        # Mock boot time
        mock_boot_time.return_value = 1640995200.0  # Unix timestamp
        
        response = await get_metrics()
        
        # Verify response structure
        assert isinstance(response.timestamp, datetime)
        assert response.streams["alert_streams"] == 5
        assert response.streams["telemetry_streams"] == 3
        assert response.uptime == 1640995200.0
        assert response.version == "1.0.0"
        
        # Verify memory info
        assert response.memory["total"] == 8589934592
        assert response.memory["available"] == 4294967296
        assert response.memory["percent"] == 50.0
        assert response.memory["used"] == 4294967296
        assert response.memory["free"] == 4294967296
    
    @pytest.mark.asyncio
    @patch('app.routes.health.stream_manager')
    @patch('app.routes.health.psutil.virtual_memory')
    @patch('app.routes.health.psutil.boot_time')
    async def test_get_metrics_exception_handling(self, mock_boot_time, mock_virtual_memory, mock_stream_manager):
        """Test metrics endpoint with exception handling."""
        # Mock stream manager to raise exception
        mock_stream_manager.get_active_streams.side_effect = Exception("Stream manager error")
        
        response = await get_metrics()
        
        # Should return default values on exception
        assert isinstance(response.timestamp, datetime)
        assert response.streams["alert_streams"] == 0
        assert response.streams["telemetry_streams"] == 0
        assert response.uptime == 0
        assert response.version == "1.0.0"
        assert response.memory == {}
    
    @pytest.mark.asyncio
    @patch('app.routes.health.stream_manager')
    @patch('app.routes.health.psutil.virtual_memory')
    @patch('app.routes.health.psutil.boot_time')
    async def test_get_metrics_no_streams(self, mock_boot_time, mock_virtual_memory, mock_stream_manager):
        """Test metrics endpoint with no active streams."""
        # Mock stream manager with no streams
        mock_stream_manager.get_active_streams.return_value = {
            "alert_streams": 0,
            "telemetry_streams": 0
        }
        
        # Mock memory info
        mock_memory = MagicMock()
        mock_memory.total = 8589934592
        mock_memory.available = 6442450944
        mock_memory.percent = 25.0
        mock_memory.used = 2147483648
        mock_memory.free = 6442450944
        mock_virtual_memory.return_value = mock_memory
        
        # Mock boot time
        mock_boot_time.return_value = 1640995200.0
        
        response = await get_metrics()
        
        assert response.streams["alert_streams"] == 0
        assert response.streams["telemetry_streams"] == 0
        assert response.memory["percent"] == 25.0
    
    @pytest.mark.asyncio
    @patch('app.routes.health.stream_manager')
    @patch('app.routes.health.psutil.virtual_memory')
    @patch('app.routes.health.psutil.boot_time')
    async def test_get_metrics_memory_calculation(self, mock_boot_time, mock_virtual_memory, mock_stream_manager):
        """Test memory calculation accuracy."""
        # Mock stream manager
        mock_stream_manager.get_active_streams.return_value = {
            "alert_streams": 1,
            "telemetry_streams": 1
        }
        
        # Mock memory with specific values
        mock_memory = MagicMock()
        mock_memory.total = 1000000000  # 1GB
        mock_memory.available = 600000000  # 600MB
        mock_memory.percent = 40.0
        mock_memory.used = 400000000  # 400MB
        mock_memory.free = 600000000  # 600MB
        mock_virtual_memory.return_value = mock_memory
        
        # Mock boot time
        mock_boot_time.return_value = 1640995200.0
        
        response = await get_metrics()
        
        # Verify memory calculations
        assert response.memory["total"] == 1000000000
        assert response.memory["available"] == 600000000
        assert response.memory["used"] == 400000000
        assert response.memory["free"] == 600000000
        assert response.memory["percent"] == 40.0
        
        # Verify total = used + free
        assert response.memory["total"] == response.memory["used"] + response.memory["free"]
    
    @pytest.mark.asyncio
    @patch('app.routes.health.stream_manager')
    @patch('app.routes.health.psutil.virtual_memory')
    @patch('app.routes.health.psutil.boot_time')
    async def test_get_metrics_timestamp_consistency(self, mock_boot_time, mock_virtual_memory, mock_stream_manager):
        """Test that timestamp is consistent across calls."""
        # Mock dependencies
        mock_stream_manager.get_active_streams.return_value = {
            "alert_streams": 0,
            "telemetry_streams": 0
        }
        mock_virtual_memory.return_value = MagicMock()
        mock_boot_time.return_value = 1640995200.0
        
        # Get two responses
        response1 = await get_metrics()
        response2 = await get_metrics()
        
        # Timestamps should be different (real time)
        assert response1.timestamp != response2.timestamp
        
        # But both should be recent
        now = datetime.utcnow()
        time_diff1 = abs((now - response1.timestamp).total_seconds())
        time_diff2 = abs((now - response2.timestamp).total_seconds())
        
        assert time_diff1 < 5  # Within 5 seconds
        assert time_diff2 < 5  # Within 5 seconds
