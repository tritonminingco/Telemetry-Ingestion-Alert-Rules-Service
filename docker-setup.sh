#!/bin/bash

# DSG Telemetry Service - Docker Setup Script
# This script sets up and runs the entire application stack

set -e

echo "🚀 DSG Telemetry Service - Docker Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it first."
    exit 1
fi

print_status "Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_success "Created .env file from .env.example"
    print_warning "Please edit .env file with your configuration before continuing"
    echo "Press Enter to continue or Ctrl+C to edit .env first..."
    read
else
    print_success ".env file already exists"
fi

print_status "Stopping any existing containers..."
docker-compose down --remove-orphans

print_status "Building and starting services..."
docker-compose up -d --build

print_status "Waiting for PostgreSQL to be ready..."
sleep 10

# Wait for PostgreSQL to be healthy
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U dsg_user -d dsg_telemetry > /dev/null 2>&1; then
        print_success "PostgreSQL is ready!"
        break
    fi
    print_status "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    print_error "PostgreSQL failed to start within expected time"
    docker-compose logs postgres
    exit 1
fi

print_status "Running database migrations..."
docker-compose exec -T app alembic upgrade head

print_status "Seeding initial data..."
docker-compose exec -T app python -m app.scripts.seed

print_success "Setup completed successfully!"
echo ""
echo "🎯 Services are now running:"
echo "  • Main API: http://localhost:8001"
echo "  • API Docs: http://localhost:8001/docs"
echo "  • pgAdmin: http://localhost:8082 (admin@dsg.com / admin123)"
echo "  • PostgreSQL: localhost:5435"
echo "  • Redis: localhost:6381"
echo ""
echo "📋 Useful commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Restart services: docker-compose restart"
echo "  • Rebuild: docker-compose up -d --build"
echo ""
echo "🔍 To view API logs in real-time:"
echo "  docker-compose logs -f app"
echo ""
echo "🧪 Test the API:"
echo "  curl -X GET http://localhost:8001/api/health/healthz"
