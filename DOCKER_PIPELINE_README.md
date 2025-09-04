# Docker Build + Push Pipeline

## 🐳 Overview

Automated Docker build and push pipeline for the DSG Telemetry Service with multi-platform support, security scanning, and comprehensive testing.

## 📁 Files

- `.github/workflows/docker-build.yml` - Main Docker pipeline (GitHub Container Registry)
- `.github/workflows/docker-hub-push.yml` - Docker Hub pipeline
- `scripts/docker-operations.sh` - Local Docker operations script

## 🚀 Features

- ✅ **Multi-platform builds** (linux/amd64, linux/arm64)
- ✅ **Automated testing** and security scanning
- ✅ **GitHub Container Registry** and **Docker Hub** support
- ✅ **Caching** for faster builds
- ✅ **Version tagging** and metadata management
- ✅ **Integration testing** with Docker Compose

## 🔧 Quick Start

### Local Usage
```bash
# Build image
./scripts/docker-operations.sh build -t v1.0.0

# Test image
./scripts/docker-operations.sh test

# Push to registry
./scripts/docker-operations.sh push -r ghcr.io/username -p

# All operations
./scripts/docker-operations.sh all -t v1.0.0 -r ghcr.io/username -p
```

### CI/CD Pipeline
- **Triggers**: Push to main/develop, version tags, pull requests
- **Registry**: GitHub Container Registry (automatic), Docker Hub (optional)
- **Security**: Trivy vulnerability scanning
- **Testing**: App import, health checks, integration tests

## 🔑 Required Secrets

For Docker Hub (optional):
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token

## 📋 Usage Examples

### Build for Development
```bash
./scripts/docker-operations.sh build -t dev
```

### Build and Push Release
```bash
./scripts/docker-operations.sh all -t v1.0.0 -r ghcr.io/username -p
```

### Run Locally
```bash
./scripts/docker-operations.sh run -t latest
```

## 🏷️ Tagging Strategy

- **Branch tags**: `main`, `develop`
- **Version tags**: `v1.0.0`, `v1.0`
- **Commit tags**: `main-sha-abc123`
- **Latest tag**: Updated for version releases

## 🔒 Security

- **Trivy scanning**: Vulnerability detection
- **Non-root user**: Secure container execution
- **Minimal base image**: Reduced attack surface

## 🚨 Troubleshooting

```bash
# Check Docker setup
docker info
docker buildx ls

# Clean up resources
./scripts/docker-operations.sh clean

# Debug container
docker run --rm -it telemetry-service:latest bash
```

## 📊 Monitoring

- **GitHub Actions**: Build logs and test results
- **Security tab**: Vulnerability scan reports
- **Registry**: Image availability and tags

The Docker build + push pipeline is ready to use! 🚀
