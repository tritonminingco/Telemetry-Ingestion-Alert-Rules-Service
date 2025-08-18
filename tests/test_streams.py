import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.routes.streams import stream_alerts, stream_telemetry
from app.stream_manager import StreamManager


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = MagicMock()
    request.is_disconnected.return_value = False
    request.send_json = AsyncMock()
    return request


@pytest.fixture
def stream_manager():
    """Create a fresh stream manager instance."""
    return StreamManager()


class TestStreamManager:
    """Test cases for StreamManager class."""
    
    @pytest.mark.asyncio
    async def test_add_alert_stream(self, stream_manager):
        """Test adding alert stream."""
        request = MagicMock()
        
        await stream_manager.add_alert_stream("AUV-001", request)
        
        assert "AUV-001" in stream_manager.alert_streams
        assert request in stream_manager.alert_streams["AUV-001"]
        assert len(stream_manager.alert_streams["AUV-001"]) == 1
    
    @pytest.mark.asyncio
    async def test_add_telemetry_stream(self, stream_manager):
        """Test adding telemetry stream."""
        request = MagicMock()
        
        await stream_manager.add_telemetry_stream("AUV-001", request)
        
        assert "AUV-001" in stream_manager.telemetry_streams
        assert request in stream_manager.telemetry_streams["AUV-001"]
        assert len(stream_manager.telemetry_streams["AUV-001"]) == 1
    
    @pytest.mark.asyncio
    async def test_add_multiple_streams(self, stream_manager):
        """Test adding multiple streams for same AUV."""
        request1 = MagicMock()
        request2 = MagicMock()
        
        await stream_manager.add_alert_stream("AUV-001", request1)
        await stream_manager.add_alert_stream("AUV-001", request2)
        
        assert len(stream_manager.alert_streams["AUV-001"]) == 2
        assert request1 in stream_manager.alert_streams["AUV-001"]
        assert request2 in stream_manager.alert_streams["AUV-001"]
    
    @pytest.mark.asyncio
    async def test_remove_alert_stream(self, stream_manager):
        """Test removing alert stream."""
        request = MagicMock()
        
        # Add stream
        await stream_manager.add_alert_stream("AUV-001", request)
        assert len(stream_manager.alert_streams["AUV-001"]) == 1
        
        # Remove stream
        await stream_manager.remove_alert_stream("AUV-001", request)
        assert "AUV-001" not in stream_manager.alert_streams
    
    @pytest.mark.asyncio
    async def test_remove_telemetry_stream(self, stream_manager):
        """Test removing telemetry stream."""
        request = MagicMock()
        
        # Add stream
        await stream_manager.add_telemetry_stream("AUV-001", request)
        assert len(stream_manager.telemetry_streams["AUV-001"]) == 1
        
        # Remove stream
        await stream_manager.remove_telemetry_stream("AUV-001", request)
        assert "AUV-001" not in stream_manager.telemetry_streams
    
    @pytest.mark.asyncio
    async def test_send_alert_event(self, stream_manager):
        """Test sending alert event."""
        request = MagicMock()
        request.is_disconnected.return_value = False
        request.send_json = AsyncMock()
        
        # Add stream
        await stream_manager.add_alert_stream("AUV-001", request)
        
        # Create alert event
        from app.schemas import AlertEvent
        event = AlertEvent(
            id="alert-1",
            timestamp=datetime.utcnow(),
            auv_id="AUV-001",
            severity="high",
            title="Test Alert",
            message="Test message"
        )
        
        # Send event
        await stream_manager.send_alert_event(event, "AUV-001")
        
        # Verify event was sent
        request.send_json.assert_called_once()
        sent_data = request.send_json.call_args[0][0]
        assert sent_data["id"] == "alert-1"
        assert sent_data["auv_id"] == "AUV-001"
        assert sent_data["severity"] == "high"
        assert sent_data["title"] == "Test Alert"
    
    @pytest.mark.asyncio
    async def test_send_telemetry_event(self, stream_manager):
        """Test sending telemetry event."""
        request = MagicMock()
        request.is_disconnected.return_value = False
        request.send_json = AsyncMock()
        
        # Add stream
        await stream_manager.add_telemetry_stream("AUV-001", request)
        
        # Create telemetry event
        from app.schemas import TelemetryEvent, Position, Environment, Plume, Battery
        event = TelemetryEvent(
            id="telemetry-1",
            timestamp=datetime.utcnow(),
            auv_id="AUV-001",
            position=Position(lat=-14.6572, lng=-125.4251, depth=3210, speed=1.5, heading=180),
            env=Environment(turbidity_ntu=8.7, sediment_mg_l=12.3, dissolved_oxygen_mg_l=6.8, temperature_c=4.3),
            plume=Plume(concentration_mg_l=52.0),
            battery=Battery(level_pct=32, voltage_v=44.5)
        )
        
        # Send event
        await stream_manager.send_telemetry_event(event, "AUV-001")
        
        # Verify event was sent
        request.send_json.assert_called_once()
        sent_data = request.send_json.call_args[0][0]
        assert sent_data["id"] == "telemetry-1"
        assert sent_data["auv_id"] == "AUV-001"
        assert sent_data["position"]["lat"] == -14.6572
        assert sent_data["position"]["lng"] == -125.4251
        assert sent_data["env"]["turbidity_ntu"] == 8.7
        assert sent_data["battery"]["level_pct"] == 32
    
    @pytest.mark.asyncio
    async def test_send_to_all_streams(self, stream_manager):
        """Test sending events to all streams."""
        request1 = MagicMock()
        request1.is_disconnected.return_value = False
        request1.send_json = AsyncMock()
        
        request2 = MagicMock()
        request2.is_disconnected.return_value = False
        request2.send_json = AsyncMock()
        
        # Add streams for different AUVs
        await stream_manager.add_alert_stream("AUV-001", request1)
        await stream_manager.add_alert_stream("AUV-002", request2)
        
        # Create alert event
        from app.schemas import AlertEvent
        event = AlertEvent(
            id="alert-1",
            timestamp=datetime.utcnow(),
            auv_id="AUV-001",
            severity="high",
            title="Test Alert",
            message="Test message"
        )
        
        # Send to all streams
        await stream_manager.send_alert_event(event)
        
        # Both requests should receive the event
        request1.send_json.assert_called_once()
        request2.send_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnected_client_handling(self, stream_manager):
        """Test handling of disconnected clients."""
        request = MagicMock()
        request.is_disconnected.return_value = True  # Client disconnected
        request.send_json = AsyncMock()
        
        # Add stream
        await stream_manager.add_alert_stream("AUV-001", request)
        
        # Create alert event
        from app.schemas import AlertEvent
        event = AlertEvent(
            id="alert-1",
            timestamp=datetime.utcnow(),
            auv_id="AUV-001",
            severity="high",
            title="Test Alert",
            message="Test message"
        )
        
        # Send event
        await stream_manager.send_alert_event(event, "AUV-001")
        
        # Event should not be sent to disconnected client
        request.send_json.assert_not_called()
        
        # Stream should be removed
        assert "AUV-001" not in stream_manager.alert_streams
    
    @pytest.mark.asyncio
    async def test_get_active_streams(self, stream_manager):
        """Test getting active stream counts."""
        request1 = MagicMock()
        request2 = MagicMock()
        request3 = MagicMock()
        
        # Add streams
        await stream_manager.add_alert_stream("AUV-001", request1)
        await stream_manager.add_alert_stream("AUV-002", request2)
        await stream_manager.add_telemetry_stream("AUV-001", request3)
        
        # Get counts
        counts = stream_manager.get_active_streams()
        
        assert counts["alert_streams"] == 2
        assert counts["telemetry_streams"] == 1
    
    @pytest.mark.asyncio
    async def test_close_all_streams(self, stream_manager):
        """Test closing all streams."""
        request1 = MagicMock()
        request2 = MagicMock()
        
        # Add streams
        await stream_manager.add_alert_stream("AUV-001", request1)
        await stream_manager.add_telemetry_stream("AUV-002", request2)
        
        # Verify streams exist
        assert len(stream_manager.alert_streams) > 0
        assert len(stream_manager.telemetry_streams) > 0
        
        # Close all streams
        await stream_manager.close_all_streams()
        
        # Verify streams are cleared
        assert len(stream_manager.alert_streams) == 0
        assert len(stream_manager.telemetry_streams) == 0


class TestStreamEndpoints:
    """Test cases for stream endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.routes.streams.stream_manager')
    async def test_stream_alerts_basic(self, mock_stream_manager, mock_request):
        """Test basic alert streaming."""
        # Mock stream manager
        mock_stream_manager.add_alert_stream = AsyncMock()
        mock_stream_manager.remove_alert_stream = AsyncMock()
        
        # Call the endpoint
        response = await stream_alerts(request=mock_request, auv_id="AUV-001")
        
        # Verify response is EventSourceResponse
        assert hasattr(response, 'body_iterator')
        
        # Verify stream was added
        mock_stream_manager.add_alert_stream.assert_called_once_with("AUV-001", mock_request)
    
    @pytest.mark.asyncio
    @patch('app.routes.streams.stream_manager')
    async def test_stream_telemetry_basic(self, mock_stream_manager, mock_request):
        """Test basic telemetry streaming."""
        # Mock stream manager
        mock_stream_manager.add_telemetry_stream = AsyncMock()
        mock_stream_manager.remove_telemetry_stream = AsyncMock()
        
        # Call the endpoint
        response = await stream_telemetry(request=mock_request, auv_id="AUV-001")
        
        # Verify response is EventSourceResponse
        assert hasattr(response, 'body_iterator')
        
        # Verify stream was added
        mock_stream_manager.add_telemetry_stream.assert_called_once_with("AUV-001", mock_request)
    
    @pytest.mark.asyncio
    @patch('app.routes.streams.stream_manager')
    async def test_stream_alerts_no_auv_filter(self, mock_stream_manager, mock_request):
        """Test alert streaming without AUV filter."""
        # Mock stream manager
        mock_stream_manager.add_alert_stream = AsyncMock()
        mock_stream_manager.remove_alert_stream = AsyncMock()
        
        # Call the endpoint without auv_id
        response = await stream_alerts(request=mock_request, auv_id=None)
        
        # Verify stream was added with None auv_id
        mock_stream_manager.add_alert_stream.assert_called_once_with(None, mock_request)
    
    @pytest.mark.asyncio
    @patch('app.routes.streams.stream_manager')
    async def test_stream_telemetry_no_auv_filter(self, mock_stream_manager, mock_request):
        """Test telemetry streaming without AUV filter."""
        # Mock stream manager
        mock_stream_manager.add_telemetry_stream = AsyncMock()
        mock_stream_manager.remove_telemetry_stream = AsyncMock()
        
        # Call the endpoint without auv_id
        response = await stream_telemetry(request=mock_request, auv_id=None)
        
        # Verify stream was added with None auv_id
        mock_stream_manager.add_telemetry_stream.assert_called_once_with(None, mock_request)
    
    @pytest.mark.asyncio
    @patch('app.routes.streams.stream_manager')
    async def test_stream_disconnection_handling(self, mock_stream_manager, mock_request):
        """Test handling of client disconnection."""
        # Mock stream manager
        mock_stream_manager.add_alert_stream = AsyncMock()
        mock_stream_manager.remove_alert_stream = AsyncMock()
        
        # Mock request to simulate disconnection
        mock_request.is_disconnected.return_value = True
        
        # Call the endpoint
        response = await stream_alerts(request=mock_request, auv_id="AUV-001")
        
        # Verify stream was added and then removed
        mock_stream_manager.add_alert_stream.assert_called_once_with("AUV-001", mock_request)
        # Note: remove_alert_stream would be called in the finally block of the generator
