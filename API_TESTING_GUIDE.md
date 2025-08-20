# DSG Telemetry Service - API Testing Guide

## 🚀 Quick Start

### 1. Run the Complete Test Suite
```bash
./test-api.sh
```

### 2. View Real-time Logs
```bash
./watch-logs.sh
```

### 3. Access Swagger UI
Open your browser and go to: `http://localhost:8001/docs`

## 📋 Available Endpoints

### Basic Endpoints
- `GET /` - Root endpoint (health check)
- `GET /api/health/healthz` - Health check
- `GET /api/health/readyz` - Readiness check
- `GET /api/health/metrics` - Metrics endpoint

### Authentication Endpoints
- `POST /api/auth/token` - Create authentication token
- `GET /api/auth/validate` - Validate token

### Telemetry Endpoints
- `POST /api/telemetry/ingest` - Ingest telemetry data
- `GET /api/telemetry/` - Get telemetry data

### Zones Endpoints
- `GET /api/zones/` - Get zones as GeoJSON
- `GET /api/zones/list` - List all zones
- `GET /api/zones/routes` - Get AUV routes

### Export Endpoints
- `GET /api/exports/isa/hourly` - Export ISA hourly data as CSV

### Stream Endpoints
- `GET /api/stream/alerts` - Stream alerts
- `GET /api/stream/telemetry` - Stream telemetry

## 🧪 Manual Testing Examples

### 1. Test Root Endpoint
```bash
curl http://localhost:8001/
```

### 2. Test Health Check
```bash
curl http://localhost:8001/api/health/healthz
```

### 3. Create Authentication Token
```bash
curl -X POST http://localhost:8001/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "test_password"}'
```

### 4. Ingest Telemetry Data
```bash
curl -X POST http://localhost:8001/api/telemetry/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-01-01T12:00:00Z",
    "auv_id": "test_auv_001",
    "position": {
      "lat": 1.0,
      "lng": 1.0,
      "depth": 10.0,
      "speed": 2.0,
      "heading": 90.0
    },
    "env": {
      "sediment_mg_l": 5.0,
      "turbidity_ntu": 2.0,
      "dissolved_oxygen_mg_l": 8.0,
      "temperature_c": 25.0
    },
    "plume": {
      "concentration_mg_l": 0.1
    },
    "battery": {
      "level_pct": 80.0,
      "voltage_v": 24.0
    }
  }'
```

### 5. Get Telemetry Data
```bash
curl "http://localhost:8001/api/telemetry/?limit=5"
```

### 6. Get Zones
```bash
curl http://localhost:8001/api/zones/
```

### 7. Get AUV Routes
```bash
curl "http://localhost:8001/api/zones/routes?auv_id=test_auv_001&from=2024-01-01T00:00:00Z&to=2024-01-01T23:59:59Z"
```

### 8. Export Data
```bash
curl "http://localhost:8001/api/exports/isa/hourly?from=2024-01-01T00:00:00Z&to=2024-01-01T23:59:59Z"
```

## 🔍 Testing with Swagger UI

1. Open `http://localhost:8001/docs` in your browser
2. You'll see all available endpoints with documentation
3. Click on any endpoint to expand it
4. Click "Try it out" to test the endpoint
5. Fill in the required parameters
6. Click "Execute" to run the test

## 📊 Testing Different Scenarios

### Valid Data Testing
- Test with complete, valid telemetry data
- Test with different AUV IDs
- Test with various environmental conditions

### Edge Case Testing
- Test with missing required fields (should return 422)
- Test with invalid data types (should return 422)
- Test with empty requests (should return 422)

### Performance Testing
- Test with large datasets
- Test concurrent requests
- Test rate limiting (if enabled)

## 🐛 Debugging

### View Application Logs
```bash
# View all logs
docker-compose logs -f

# View only API logs
docker-compose logs -f app

# View database logs
docker-compose logs -f postgres
```

### Check Service Status
```bash
# Check if all services are running
docker-compose ps

# Restart services if needed
docker-compose restart
```

### Database Queries
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U dsg_user -d dsg_telemetry

# Check tables
\dt

# Check telemetry data
SELECT COUNT(*) FROM telemetry;

# Check alerts
SELECT COUNT(*) FROM alerts;
```

## 🔧 Custom Test Scripts

### Create Your Own Test
```bash
#!/bin/bash
# Custom test example

echo "Testing custom scenario..."

# Your test logic here
response=$(curl -s -w "%{http_code}" -X POST http://localhost:8001/api/telemetry/ingest \
  -H "Content-Type: application/json" \
  -d '{"your": "data"}')

status_code="${response: -3}"
body="${response%???}"

if [ "$status_code" = "201" ]; then
    echo "✅ Test passed"
else
    echo "❌ Test failed: $status_code"
    echo "Response: $body"
fi
```

## 📈 Monitoring

### Health Checks
- Monitor `/api/health/healthz` for service health
- Monitor `/api/health/readyz` for readiness
- Monitor `/api/health/metrics` for performance metrics

### Log Analysis
- Look for ERROR level logs
- Monitor response times
- Check for failed requests

## 🚨 Common Issues and Solutions

### 1. Service Not Running
```bash
# Start all services
./docker-setup.sh
```

### 2. Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready -U dsg_user -d dsg_telemetry

# Restart database
docker-compose restart postgres
```

### 3. Authentication Issues
- Verify authentication is disabled for testing (currently disabled)
- Check token format if using authentication
- Ensure proper headers are set

### 4. Data Validation Errors
- Check required fields in request payload
- Verify data types match schema
- Ensure proper JSON format

## 📝 Test Data Examples

### Sample Telemetry Data
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "auv_id": "AUV-001",
  "position": {
    "lat": -14.6572,
    "lng": -125.4251,
    "depth": 3210,
    "speed": 1.5,
    "heading": 180
  },
  "env": {
    "turbidity_ntu": 8.7,
    "sediment_mg_l": 12.3,
    "dissolved_oxygen_mg_l": 6.8,
    "temperature_c": 4.3
  },
  "plume": {
    "concentration_mg_l": 52.0
  },
  "battery": {
    "level_pct": 32,
    "voltage_v": 44.5
  }
}
```

### Sample Export Query
```
GET /api/exports/isa/hourly?from=2024-01-01T00:00:00Z&to=2024-01-01T23:59:59Z&auv_id=AUV-001
```

## ✅ Success Criteria

A successful test run should show:
- All endpoints returning expected status codes
- Valid JSON responses for GET requests
- Proper error messages for invalid requests
- No authentication errors (when disabled)
- Consistent response times
- No database connection errors

## 🔄 Continuous Testing

For continuous integration, you can:
1. Run `./test-api.sh` in your CI/CD pipeline
2. Set up automated health checks
3. Monitor endpoint availability
4. Track response times and error rates

---

**Note**: Authentication is currently disabled for testing purposes. When ready to enable authentication, update the middleware and endpoint configurations accordingly.
