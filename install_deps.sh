#!/bin/bash

# DSG Telemetry Service - Dependency Installation Script
# This script handles the installation of dependencies for Python 3.11+

set -e

echo "🚀 Installing DSG Telemetry Service dependencies..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
echo "📋 Python version detected: $PYTHON_VERSION"

# Upgrade pip and install setuptools first
echo "📦 Upgrading pip and installing setuptools..."
python3 -m pip install --upgrade pip setuptools wheel

# Install system dependencies (if on Ubuntu/Debian)
if command -v apt-get &> /dev/null; then
    echo "🔧 Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gdal-bin \
        libgdal-dev \
        gcc \
        g++
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo "✅ Dependencies installed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Copy .env.example to .env and configure your settings"
echo "2. Start the database: docker-compose up -d postgres"
echo "3. Run migrations: docker-compose exec app alembic upgrade head"
echo "4. Start the application: docker-compose up -d"
