# DSG Telemetry Service

A high-performance backend service for AUV (Autonomous Underwater Vehicle) telemetry ingestion and alert rule evaluation, built with FastAPI, SQLAlchemy, and TimescaleDB.

## 🚀 Features

- **Real-time Telemetry Ingestion**: Handle 1,000+ messages per second with batch processing
- **Alert Rules Engine**: Configurable threshold, proximity, and zone-based alert rules
- **Live Streaming**: Server-Sent Events (SSE) for real-time alerts and telemetry
- **Geospatial Support**: Zone management and AUV route tracking with GeoJSON
- **ISA Export**: CSV export functionality for regulatory reporting
- **Authentication**: Token-based API security
- **Rate Limiting**: Configurable request rate limiting
- **Health Monitoring**: Comprehensive health checks and metrics
- **Containerized**: Docker and Docker Compose for easy deployment

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AUV Devices   │───▶│  Telemetry API  │───▶│  TimescaleDB    │
│                 │    │   (FastAPI)     │    │   (Hypertable)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Alert Engine   │
                       │   (Rules)       │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  SSE Streams    │───▶│   UI Clients    │
                       │  (Real-time)    │    │   (Web/Mobile)  │
                       └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+ with PostGIS extension
- Redis (for caching and Celery)

## 🛠️ Installation

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd dsg-telemetry-service
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**:
   ```bash
   docker-compose exec app alembic upgrade head
   docker-compose exec app python -m app.scripts.seed
   ```

### Option 2: Local Development

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**:
   ```bash
   # Start PostgreSQL and Redis
   # Update .env with database connection details
   ```

4. **Run migrations**:
   ```bash
   alembic upgrade head
   python -m app.scripts.seed
   ```

5. **Start the service**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🔧 Configuration

### Environment Variables

```bash
# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost/dsg_telemetry
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
AUTH_TOKEN=your-secure-auth-token

# Performance
BATCH_SIZE=100
BATCH_TIMEOUT_MS=1000
RATE_LIMIT_MAX=1000
RATE_LIMIT_WINDOW_SECONDS=60

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Metrics
METRICS_ENABLED=true
METRICS_PORT=9090
```

## 📚 API Documentation

### Authentication

All API endpoints require authentication using a Bearer token:

```bash
Authorization: Bearer your-auth-token
```

### Core Endpoints

#### 1. Telemetry Ingestion

**POST** `/api/telemetry/ingest`

Ingest AUV telemetry data and evaluate alert rules.

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
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
  "species_detections": [
    {
      "name": "Benthic Octopod",
      "distance_m": 150.0
    }
  ],
  "battery": {
    "level_pct": 32,
    "voltage_v": 44.5
  }
}
```

#### 2. Real-time Streaming

**GET** `/api/stream/alerts?auv_id=AUV-001`

Stream live alerts via Server-Sent Events.

**GET** `/api/stream/telemetry?auv_id=AUV-001`

Stream live telemetry data via Server-Sent Events.

#### 3. Zones and Routes

**GET** `/api/zones/`

Get all zones as GeoJSON FeatureCollection.

**GET** `/api/zones/routes?auv_id=AUV-001&from=2025-01-15T00:00:00Z&to=2025-01-15T23:59:59Z`

Get AUV route as polyline points.

#### 4. Data Export

**GET** `/api/exports/isa/hourly?from=2025-01-15T00:00:00Z&to=2025-01-15T23:59:59Z&auv_id=AUV-001`

Export ISA-compliant CSV data.

#### 5. Health and Metrics

**GET** `/api/health/healthz`

Health check endpoint.

**GET** `/api/health/readyz`

Readiness check endpoint.

**GET** `/api/health/metrics`

Application metrics.

### Alert Rules

The service supports three types of alert rules:

#### 1. Threshold Rules

```json
{
  "id": "RULE-SEDIMENT-01",
  "type": "threshold",
  "config": {
    "path": "env.sediment_mg_l",
    "operator": ">",
    "value": 25.0,
    "severity": "high",
    "dedupe_window_sec": 300
  }
}
```

#### 2. Proximity Rules

```json
{
  "id": "RULE-SPECIES-01",
  "type": "proximity",
  "config": {
    "path": "species_detections[].distance_m",
    "operator": "<",
    "value": 150.0,
    "severity": "high",
    "dedupe_window_sec": 600
  }
}
```

#### 3. Zone Dwell Rules

```json
{
  "id": "RULE-ZONE-01",
  "type": "zone_dwell",
  "config": {
    "zone_type": "sensitive",
    "max_minutes": 60,
    "severity": "medium",
    "dedupe_window_sec": 1800
  }
}
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_telemetry.py

# Run load tests
python scripts/load_test.py --rate 1000 --duration 60
```

### Test Coverage

The test suite covers:
- ✅ Telemetry ingestion and validation
- ✅ Alert rule evaluation
- ✅ Database operations
- ✅ API endpoints
- ✅ Authentication and rate limiting
- ✅ SSE streaming
- ✅ CSV export functionality
- ✅ Health checks and metrics

## 📊 Performance

### Load Testing

The service is designed to handle:
- **1,000 messages/second** for 60 seconds without dropping data
- **Batch processing** for optimal database performance
- **Connection pooling** for efficient database usage
- **Rate limiting** to prevent abuse

### Monitoring

Monitor the service using:
- **Health endpoints**: `/api/health/healthz` and `/api/health/readyz`
- **Metrics endpoint**: `/api/health/metrics`
- **Application logs**: Structured JSON logging
- **Database metrics**: PostgreSQL performance and query statistics

## 🚀 Deployment

### Production Deployment

1. **Build Docker image**:
   ```bash
   docker build -t dsg-telemetry-service .
   ```

2. **Deploy with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Set up reverse proxy** (nginx):
   ```nginx
   upstream dsg_backend {
       server localhost:8000;
   }

   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://dsg_backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests.

## 🔒 Security

- **Authentication**: Token-based API security
- **Rate Limiting**: Configurable per-client rate limits
- **CORS**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

## 📈 Monitoring and Logging

### Logging

The service uses structured logging with configurable levels:

```python
import structlog

logger = structlog.get_logger()
logger.info("Telemetry ingested", auv_id="AUV-001", alerts_generated=2)
```

### Metrics

Available metrics include:
- Active SSE stream counts
- System memory usage
- Application uptime
- Request rates and response times

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs` when the service is running
- Review the test examples for usage patterns

## 🔄 Changelog

### v1.0.0
- Initial release
- Telemetry ingestion and alert evaluation
- Real-time SSE streaming
- Geospatial zone and route management
- ISA export functionality
- Comprehensive test suite
- Docker containerization
