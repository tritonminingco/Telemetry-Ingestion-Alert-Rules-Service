# Docker Build + Push Pipeline Guide

This guide explains the Docker build and push pipeline implementation for the DSG Telemetry Service.

## 🐳 Overview

The Docker pipeline provides automated building, testing, and pushing of Docker images with the following features:

- **Multi-platform builds** (linux/amd64, linux/arm64)
- **Automated testing** of built images
- **Security scanning** with Trivy
- **Integration testing** with Docker Compose
- **Multiple registry support** (GitHub Container Registry, Docker Hub)
- **Caching** for faster builds
- **Version tagging** and metadata management

## 📁 Files Created

### GitHub Actions Workflows
- `.github/workflows/docker-build.yml` - Main Docker build pipeline (GitHub Container Registry)
- `.github/workflows/docker-hub-push.yml` - Docker Hub push pipeline

### Scripts
- `scripts/docker-operations.sh` - Local Docker operations helper script

### Documentation
- `DOCKER_PIPELINE_GUIDE.md` - This guide

## 🚀 Pipeline Features

### 1. Automated Build Process
- **Triggered on**: Push to main/develop branches, version tags, pull requests
- **Multi-platform**: Builds for linux/amd64 and linux/arm64
- **Caching**: Uses GitHub Actions cache for faster builds
- **BuildKit**: Leverages Docker BuildKit for advanced features

### 2. Testing & Validation
- **Image testing**: Verifies app can be imported and basic functionality works
- **Health checks**: Tests health endpoint availability
- **Integration testing**: Full Docker Compose environment testing
- **Security scanning**: Trivy vulnerability scanning

### 3. Registry Management
- **GitHub Container Registry**: Primary registry (ghcr.io)
- **Docker Hub**: Alternative registry support
- **Tagging strategy**: Branch names, version tags, commit SHAs
- **Latest tag**: Automatic latest tag updates for version releases

## 🔧 Setup Instructions

### Prerequisites

1. **Docker installed** on your local machine
2. **GitHub repository** with Actions enabled
3. **Registry credentials** (if using private registries)

### GitHub Secrets Required

For **GitHub Container Registry** (automatic):
- No additional secrets needed (uses `GITHUB_TOKEN`)

For **Docker Hub**:
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password/token

### Local Development Setup

1. **Install Docker Buildx**:
   ```bash
   docker buildx create --use
   ```

2. **Make script executable**:
   ```bash
   chmod +x scripts/docker-operations.sh
   ```

## 📋 Usage

### Local Docker Operations

The `scripts/docker-operations.sh` script provides easy local Docker operations:

#### Build Image
```bash
# Build with default settings
./scripts/docker-operations.sh build

# Build with custom tag
./scripts/docker-operations.sh build -t v1.0.0

# Build for multiple platforms
./scripts/docker-operations.sh build --platforms "linux/amd64,linux/arm64"
```

#### Test Image
```bash
# Test built image
./scripts/docker-operations.sh test

# Test specific tag
./scripts/docker-operations.sh test -t v1.0.0
```

#### Push to Registry
```bash
# Push to GitHub Container Registry
./scripts/docker-operations.sh push -r ghcr.io/username

# Push to Docker Hub
./scripts/docker-operations.sh push -r username

# Build and push in one command
./scripts/docker-operations.sh all -t v1.0.0 -r ghcr.io/username -p
```

#### Run Container Locally
```bash
# Run container with default settings
./scripts/docker-operations.sh run

# Run specific tag
./scripts/docker-operations.sh run -t v1.0.0
```

#### Clean Up
```bash
# Clean Docker resources
./scripts/docker-operations.sh clean
```

### CI/CD Pipeline Usage

#### Automatic Triggers
- **Push to main/develop**: Builds and tests image
- **Version tags (v*)**: Builds, tests, and pushes to registry
- **Pull requests**: Builds and tests (no push)

#### Manual Triggers
- **Docker Hub workflow**: Can be triggered manually via GitHub Actions

## 🏗️ Build Process

### 1. Build Stage
```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: ${{ github.event_name != 'pull_request' }}
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 2. Testing Stage
- **App import test**: Verifies Python app can be imported
- **Health check test**: Tests health endpoint availability
- **Integration test**: Full Docker Compose environment

### 3. Security Stage
- **Trivy scanning**: Vulnerability scanning of built image
- **SARIF output**: Results uploaded to GitHub Security tab

### 4. Push Stage
- **Conditional push**: Only pushes on main branch (not PRs)
- **Multi-platform**: Pushes all platform variants
- **Tagging**: Automatic tag generation based on git events

## 🏷️ Tagging Strategy

### Automatic Tags
- **Branch tags**: `main`, `develop`
- **Version tags**: `v1.0.0`, `v1.0`
- **Commit tags**: `main-sha-abc123`

### Manual Tags
- **Latest tag**: Updated for version releases
- **Custom tags**: Can be added manually

## 🔒 Security Features

### Vulnerability Scanning
- **Trivy integration**: Scans built images for vulnerabilities
- **SARIF reporting**: Results in GitHub Security tab
- **Fail on high severity**: Configurable failure thresholds

### Image Security
- **Non-root user**: Application runs as non-root user
- **Minimal base image**: Uses Python slim image
- **Multi-stage builds**: Reduces attack surface

## 📊 Monitoring & Logs

### GitHub Actions
- **Build logs**: Available in Actions tab
- **Test results**: Pass/fail status for each stage
- **Security reports**: Vulnerability scan results

### Local Monitoring
- **Build progress**: Real-time build output
- **Test results**: Local test execution results
- **Registry status**: Push confirmation

## 🚨 Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check Docker daemon
docker info

# Check buildx
docker buildx ls

# Clean build cache
docker builder prune
```

#### Push Failures
```bash
# Check registry authentication
docker login ghcr.io
docker login docker.io

# Verify image exists
docker images | grep telemetry-service
```

#### Test Failures
```bash
# Check container logs
docker logs <container-id>

# Test manually
docker run --rm telemetry-service:latest python -c "import app"
```

### Debug Commands

```bash
# Inspect image
docker image inspect telemetry-service:latest

# Run with debug
docker run --rm -it telemetry-service:latest bash

# Check health endpoint
curl -f http://localhost:8000/api/health/healthz
```

## 🔄 Workflow

### Development Workflow
1. **Local development**: Use `docker-compose.yml` for local development
2. **Local testing**: Use `scripts/docker-operations.sh test`
3. **Local build**: Use `scripts/docker-operations.sh build`
4. **Push changes**: Git push triggers CI/CD pipeline

### Release Workflow
1. **Create version tag**: `git tag v1.0.0 && git push origin v1.0.0`
2. **Pipeline triggers**: Automatic build and push
3. **Registry update**: Image available in registry
4. **Deployment**: Use new image tag for deployment

## 📈 Performance Optimization

### Build Optimization
- **Layer caching**: Efficient layer reuse
- **Multi-platform**: Parallel builds for different architectures
- **BuildKit**: Advanced build features
- **Registry cache**: Cached layers from registry

### Testing Optimization
- **Parallel testing**: Multiple test stages run in parallel
- **Quick tests**: Fast validation before full testing
- **Conditional testing**: Skip tests when not needed

## 🔧 Configuration

### Environment Variables
```bash
# Registry configuration
REGISTRY=ghcr.io
IMAGE_NAME=username/telemetry-service

# Build configuration
PLATFORMS=linux/amd64,linux/arm64
BUILD_ARGS=BUILDKIT_INLINE_CACHE=1
```

### Customization
- **Base image**: Modify `Dockerfile` for different base images
- **Build args**: Add custom build arguments
- **Platforms**: Change target platforms
- **Registry**: Switch between different registries

## 📚 Additional Resources

- [Docker Buildx Documentation](https://docs.docker.com/buildx/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)

## 🎯 Next Steps

1. **Configure secrets**: Add registry credentials if needed
2. **Test locally**: Use the provided scripts for local testing
3. **Push to main**: Trigger the pipeline with a push to main branch
4. **Monitor results**: Check GitHub Actions for build status
5. **Deploy**: Use the built images for deployment

The Docker build + push pipeline is now ready to use! 🚀
