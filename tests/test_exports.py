import pytest
import csv
import io
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.routes.exports import export_isa_hourly


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    
    # Mock telemetry records
    telemetry_records = []
    for i in range(3):
        mock_record = MagicMock()
        mock_record[0] = MagicMock()  # Telemetry object
        mock_record[0].timestamp = datetime.utcnow() + timedelta(hours=i)
        mock_record[0].auv_id = f"AUV-00{i+1}"
        mock_record[0].position_lat = -14.6572 + i * 0.001
        mock_record[0].position_lng = -125.4251 + i * 0.001
        mock_record[0].depth_m = 3210 + i * 10
        mock_record[0].sediment_mg_l = 12.3 + i * 2.0
        mock_record[0].turbidity_ntu = 8.7 + i * 1.0
        mock_record[0].dissolved_oxygen_mg_l = 6.8 - i * 0.2
        mock_record[0].temperature_c = 4.3 + i * 0.5
        mock_record[0].plume_concentration_mg_l = 52.0 + i * 5.0
        mock_record[0].battery_pct = 32 - i * 5
        mock_record[1] = i  # alerts_count
        
        telemetry_records.append(mock_record)
    
    session.execute.return_value.all.return_value = telemetry_records
    return session


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = MagicMock()
    request.state.user = {"id": "test-user", "type": "service"}
    return request


class TestCSVExport:
    """Test cases for CSV export functionality."""
    
    @pytest.mark.asyncio
    async def test_export_isa_hourly_basic(self, mock_session, mock_request):
        """Test basic CSV export functionality."""
        from fastapi import Query
        
        # Test parameters
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        auv_id = None
        
        # Mock dependencies
        mock_get_async_session = AsyncMock(return_value=mock_session)
        mock_get_current_user = AsyncMock(return_value={"id": "test-user"})
        
        # Call the function
        response = await export_isa_hourly(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            auv_id=auv_id,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment" in response.headers["content-disposition"]
        
        # Parse CSV content
        csv_content = response.body.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Verify headers
        expected_headers = [
            "timestamp", "auv_id", "lat", "lng", "depth_m",
            "sediment_mg_l", "turbidity_ntu", "dissolved_oxygen_mg_l",
            "temperature_c", "plume_concentration_mg_l", "battery_pct", "alerts_count"
        ]
        assert rows[0] == expected_headers
        
        # Verify data rows
        assert len(rows) == 4  # 1 header + 3 data rows
        
        # Check first data row
        data_row = rows[1]
        assert data_row[1] == "AUV-001"  # auv_id
        assert float(data_row[5]) == 12.3  # sediment_mg_l
        assert int(data_row[11]) == 0  # alerts_count
    
    @pytest.mark.asyncio
    async def test_export_isa_hourly_with_auv_filter(self, mock_session, mock_request):
        """Test CSV export with AUV filter."""
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        auv_id = "AUV-002"
        
        response = await export_isa_hourly(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            auv_id=auv_id,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify filename contains AUV ID
        content_disposition = response.headers["content-disposition"]
        assert auv_id in content_disposition
    
    @pytest.mark.asyncio
    async def test_export_isa_hourly_filename_format(self, mock_session, mock_request):
        """Test CSV export filename format."""
        from_timestamp = datetime(2025, 8, 15, 9, 0, 0)
        to_timestamp = datetime(2025, 8, 15, 10, 0, 0)
        auv_id = "AUV-003"
        
        response = await export_isa_hourly(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            auv_id=auv_id,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify filename format
        content_disposition = response.headers["content-disposition"]
        expected_filename = f"isa_export_{auv_id}_20250815_20250815.csv"
        assert expected_filename in content_disposition
    
    @pytest.mark.asyncio
    async def test_export_isa_hourly_data_formatting(self, mock_session, mock_request):
        """Test CSV data formatting."""
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        
        response = await export_isa_hourly(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            auv_id=None,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Parse CSV content
        csv_content = response.body.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Check data formatting
        data_row = rows[1]
        
        # Check timestamp format (ISO format)
        assert 'T' in data_row[0]  # ISO format contains 'T'
        
        # Check numeric formatting
        assert float(data_row[3]) == -125.4251  # lng
        assert int(data_row[4]) == 3210  # depth_m
        assert float(data_row[5]) == 12.3  # sediment_mg_l
        assert float(data_row[6]) == 8.7  # turbidity_ntu
        assert float(data_row[7]) == 6.8  # dissolved_oxygen_mg_l
        assert float(data_row[8]) == 4.3  # temperature_c
        assert float(data_row[9]) == 52.0  # plume_concentration_mg_l
        assert int(data_row[10]) == 32  # battery_pct
        assert int(data_row[11]) == 0  # alerts_count
    
    @pytest.mark.asyncio
    async def test_export_isa_hourly_empty_result(self, mock_session, mock_request):
        """Test CSV export with empty result set."""
        # Mock empty result
        mock_session.execute.return_value.all.return_value = []
        
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        
        response = await export_isa_hourly(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            auv_id=None,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Parse CSV content
        csv_content = response.body.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Should only have headers
        assert len(rows) == 1
        assert rows[0][0] == "timestamp"  # First header
    
    @pytest.mark.asyncio
    async def test_export_isa_hourly_headers_consistency(self, mock_session, mock_request):
        """Test CSV headers consistency with requirements."""
        from_timestamp = datetime.utcnow()
        to_timestamp = from_timestamp + timedelta(hours=1)
        
        response = await export_isa_hourly(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            auv_id=None,
            session=mock_session,
            current_user={"id": "test-user"}
        )
        
        # Parse CSV content
        csv_content = response.body.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        # Verify required headers from specification
        headers = rows[0]
        required_headers = [
            "timestamp", "auv_id", "lat", "lng", "depth_m",
            "sediment_mg_l", "turbidity_ntu", "dissolved_oxygen_mg_l",
            "temperature_c", "plume_concentration_mg_l", "battery_pct", "alerts_count"
        ]
        
        assert headers == required_headers
        assert len(headers) == 12  # Exactly 12 columns as specified
