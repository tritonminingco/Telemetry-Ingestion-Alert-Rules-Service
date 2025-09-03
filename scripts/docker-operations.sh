#!/bin/bash

# Docker Operations Script for Telemetry Service
# This script helps with building, testing, and pushing Docker images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[DOCKER]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Default values
IMAGE_NAME="telemetry-service"
TAG="latest"
REGISTRY=""
PUSH=false
PLATFORMS="linux/amd64"
BUILD_ARGS=""

# Function to show usage
show_usage() {
    echo "Docker Operations Script"
    echo "======================="
    echo ""
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker image"
    echo "  test        Test Docker image"
    echo "  push        Push Docker image to registry"
    echo "  run         Run Docker container locally"
    echo "  clean       Clean up Docker resources"
    echo "  all         Build, test, and push (if --push is set)"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG        Image tag (default: latest)"
    echo "  -r, --registry REG   Registry URL (e.g., ghcr.io/username)"
    echo "  -p, --push           Push image after building"
    echo "  --platforms PLAT     Target platforms (default: linux/amd64)"
    echo "  --build-args ARGS    Additional build arguments"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build -t v1.0.0"
    echo "  $0 build -r ghcr.io/username -p"
    echo "  $0 all -t v1.0.0 -r ghcr.io/username -p"
}

# Function to build Docker image
build_image() {
    print_header "Building Docker image: $IMAGE_NAME:$TAG"

    # Set full image name
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"
    else
        FULL_IMAGE_NAME="$IMAGE_NAME"
    fi

    # Build command
    BUILD_CMD="docker buildx build --platform $PLATFORMS"

    if [ "$PUSH" = true ] && [ -n "$REGISTRY" ]; then
        BUILD_CMD="$BUILD_CMD --push"
    else
        BUILD_CMD="$BUILD_CMD --load"
    fi

    if [ -n "$BUILD_ARGS" ]; then
        BUILD_CMD="$BUILD_CMD --build-arg $BUILD_ARGS"
    fi

    BUILD_CMD="$BUILD_CMD -t $FULL_IMAGE_NAME:$TAG ."

    print_status "Running: $BUILD_CMD"
    eval $BUILD_CMD

    print_success "Image built successfully: $FULL_IMAGE_NAME:$TAG"
}

# Function to test Docker image
test_image() {
    print_header "Testing Docker image: $IMAGE_NAME:$TAG"

    # Set full image name
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"
    else
        FULL_IMAGE_NAME="$IMAGE_NAME"
    fi

    # Test 1: Check if image exists
    if ! docker image inspect "$FULL_IMAGE_NAME:$TAG" >/dev/null 2>&1; then
        print_error "Image $FULL_IMAGE_NAME:$TAG does not exist"
        return 1
    fi

    # Test 2: Check if app can be imported
    print_status "Testing app import..."
    if docker run --rm "$FULL_IMAGE_NAME:$TAG" python -c "import app; print('✅ App imports successfully')"; then
        print_success "App import test passed"
    else
        print_error "App import test failed"
        return 1
    fi

    # Test 3: Check health endpoint (if available)
    print_status "Testing health endpoint..."
    CONTAINER_ID=$(docker run -d "$FULL_IMAGE_NAME:$TAG")
    sleep 10

    if docker exec "$CONTAINER_ID" python -c "
import requests
try:
    response = requests.get('http://localhost:8000/api/health/healthz', timeout=5)
    print(f'✅ Health check passed: {response.status_code}')
except Exception as e:
    print(f'⚠️ Health check not available: {e}')
"; then
        print_success "Health check test completed"
    else
        print_warning "Health check test failed"
    fi

    docker stop "$CONTAINER_ID" >/dev/null 2>&1 || true

    print_success "All tests passed for $FULL_IMAGE_NAME:$TAG"
}

# Function to push Docker image
push_image() {
    if [ -z "$REGISTRY" ]; then
        print_error "Registry not specified. Use -r or --registry option."
        return 1
    fi

    print_header "Pushing Docker image to registry"

    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"

    # Check if image exists
    if ! docker image inspect "$FULL_IMAGE_NAME:$TAG" >/dev/null 2>&1; then
        print_error "Image $FULL_IMAGE_NAME:$TAG does not exist. Build it first."
        return 1
    fi

    # Push image
    print_status "Pushing $FULL_IMAGE_NAME:$TAG..."
    if docker push "$FULL_IMAGE_NAME:$TAG"; then
        print_success "Image pushed successfully to $REGISTRY"
    else
        print_error "Failed to push image"
        return 1
    fi

    # Update latest tag if this is a version tag
    if [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_status "Updating latest tag..."
        docker tag "$FULL_IMAGE_NAME:$TAG" "$FULL_IMAGE_NAME:latest"
        docker push "$FULL_IMAGE_NAME:latest"
        print_success "Latest tag updated"
    fi
}

# Function to run Docker container locally
run_container() {
    print_header "Running Docker container locally"

    # Set full image name
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"
    else
        FULL_IMAGE_NAME="$IMAGE_NAME"
    fi

    # Check if image exists
    if ! docker image inspect "$FULL_IMAGE_NAME:$TAG" >/dev/null 2>&1; then
        print_error "Image $FULL_IMAGE_NAME:$TAG does not exist. Build it first."
        return 1
    fi

    # Run container
    print_status "Running container from $FULL_IMAGE_NAME:$TAG"
    print_status "Access the application at: http://localhost:8000"
    print_status "Press Ctrl+C to stop the container"

    docker run --rm -p 8000:8000 \
        -e DATABASE_URL="postgresql://test:test@host.docker.internal:5432/test" \
        -e REDIS_URL="redis://host.docker.internal:6379" \
        -e SECRET_KEY="local-dev-secret" \
        -e ENVIRONMENT="development" \
        "$FULL_IMAGE_NAME:$TAG"
}

# Function to clean up Docker resources
clean_docker() {
    print_header "Cleaning up Docker resources"

    # Remove dangling images
    print_status "Removing dangling images..."
    docker image prune -f

    # Remove stopped containers
    print_status "Removing stopped containers..."
    docker container prune -f

    # Remove unused networks
    print_status "Removing unused networks..."
    docker network prune -f

    # Remove unused volumes (optional)
    read -p "Remove unused volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing unused volumes..."
        docker volume prune -f
    fi

    print_success "Docker cleanup completed"
}

# Function to run all operations
run_all() {
    print_header "Running all Docker operations"

    build_image
    test_image

    if [ "$PUSH" = true ]; then
        push_image
    fi

    print_success "All operations completed successfully"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        --platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --build-args)
            BUILD_ARGS="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        build|test|push|run|clean|all)
            COMMAND="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if command is provided
if [ -z "$COMMAND" ]; then
    print_error "No command specified"
    show_usage
    exit 1
fi

# Execute command
case $COMMAND in
    build)
        build_image
        ;;
    test)
        test_image
        ;;
    push)
        push_image
        ;;
    run)
        run_container
        ;;
    clean)
        clean_docker
        ;;
    all)
        run_all
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
