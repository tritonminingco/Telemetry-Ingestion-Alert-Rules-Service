#!/bin/bash

# Image Scanner Integration Script
# Supports Trivy and Grype vulnerability scanning

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="telemetry-service"
TAG="latest"
SCAN_TYPES=("fs" "config" "secret" "image")
SEVERITY_LEVELS=("CRITICAL" "HIGH" "MEDIUM" "LOW")
OUTPUT_FORMATS=("table" "json" "sarif")

# Functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Trivy if not present
install_trivy() {
    if ! command_exists trivy; then
        print_status "Installing Trivy..."
        # Install to user's home directory to avoid permission issues
        mkdir -p ~/.local/bin
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b ~/.local/bin v0.48.0
        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            export PATH="$HOME/.local/bin:$PATH"
        fi
        print_success "Trivy installed successfully to ~/.local/bin"
    else
        print_success "Trivy already installed"
    fi
}

# Install Grype if not present
install_grype() {
    if ! command_exists grype; then
        print_status "Installing Grype..."
        # Install to user's home directory to avoid permission issues
        mkdir -p ~/.local/bin
        curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b ~/.local/bin
        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            export PATH="$HOME/.local/bin:$PATH"
        fi
        print_success "Grype installed successfully to ~/.local/bin"
    else
        print_success "Grype already installed"
    fi
}

# Build Docker image
build_image() {
    print_header "Building Docker Image"
    docker build -t ${IMAGE_NAME}:${TAG} .
    print_success "Image built successfully: ${IMAGE_NAME}:${TAG}"
}

# Run Trivy scan
run_trivy_scan() {
    local scan_type=$1
    local severity=$2
    local output_format=$3

    print_header "Running Trivy ${scan_type} scan"

    case $scan_type in
        "fs")
            trivy fs --severity ${severity} --format ${output_format} --output trivy-${scan_type}-results.${output_format} --timeout 10m --scanners vuln .
            ;;
        "config")
            trivy config --severity ${severity} --format ${output_format} --output trivy-${scan_type}-results.${output_format} --timeout 5m .
            ;;
        "secret")
            trivy secret --severity ${severity} --format ${output_format} --output trivy-${scan_type}-results.${output_format} --timeout 5m .
            ;;
        "image")
            trivy image --severity ${severity} --format ${output_format} --output trivy-${scan_type}-results.${output_format} --timeout 15m --scanners vuln ${IMAGE_NAME}:${TAG}
            ;;
    esac

    print_success "Trivy ${scan_type} scan completed"
}

# Run Grype scan
run_grype_scan() {
    local output_format=$1

    print_header "Running Grype scan"
    grype ${IMAGE_NAME}:${TAG} --output ${output_format} --file grype-results.${output_format}
    print_success "Grype scan completed"
}

# Display scan results
display_results() {
    print_header "Scan Results Summary"

    echo "=== Trivy Results ==="
    for scan_type in "${SCAN_TYPES[@]}"; do
        for format in "${OUTPUT_FORMATS[@]}"; do
            if [ -f "trivy-${scan_type}-results.${format}" ]; then
                echo "📄 trivy-${scan_type}-results.${format}"
                if [ "$format" = "table" ]; then
                    cat "trivy-${scan_type}-results.${format}"
                fi
            fi
        done
    done

    echo "=== Grype Results ==="
    for format in "${OUTPUT_FORMATS[@]}"; do
        if [ -f "grype-results.${format}" ]; then
            echo "📄 grype-results.${format}"
            if [ "$format" = "table" ]; then
                cat "grype-results.${format}"
            fi
        fi
    done
}

# Clean up scan files
cleanup() {
    print_status "Cleaning up scan files..."
    rm -f trivy-*-results.* grype-results.*
    print_success "Cleanup completed"
}

# Main scanning function
run_comprehensive_scan() {
    print_header "Starting Comprehensive Image Security Scan"

    # Install tools if needed
    install_trivy
    install_grype

    # Build image if it doesn't exist
    if ! docker image inspect ${IMAGE_NAME}:${TAG} >/dev/null 2>&1; then
        build_image
    fi

    # Run Trivy scans
    for scan_type in "${SCAN_TYPES[@]}"; do
        for severity in "${SEVERITY_LEVELS[@]}"; do
            for format in "${OUTPUT_FORMATS[@]}"; do
                run_trivy_scan "$scan_type" "$severity" "$format"
            done
        done
    done

    # Run Grype scan
    for format in "${OUTPUT_FORMATS[@]}"; do
        run_grype_scan "$format"
    done

    # Display results
    display_results

    print_success "Comprehensive scan completed!"
}

# Quick scan function
run_quick_scan() {
    print_header "Running Quick Security Scan"

    install_trivy
    install_grype

    # Build image if needed
    if ! docker image inspect ${IMAGE_NAME}:${TAG} >/dev/null 2>&1; then
        build_image
    fi

    # Run essential scans
    run_trivy_scan "fs" "CRITICAL,HIGH" "table"
    run_trivy_scan "image" "CRITICAL,HIGH" "table"
    run_grype_scan "table"

    display_results
    print_success "Quick scan completed!"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo ""
    echo "Commands:"
    echo "  comprehensive    Run comprehensive security scan with all tools and formats"
    echo "  quick           Run quick security scan with essential checks"
    echo "  build           Build Docker image only"
    echo "  cleanup         Clean up scan result files"
    echo "  install         Install scanning tools (Trivy and Grype)"
    echo ""
    echo "Options:"
    echo "  -i, --image     Docker image name (default: telemetry-service)"
    echo "  -t, --tag       Docker image tag (default: latest)"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 quick"
    echo "  $0 comprehensive"
    echo "  $0 -i myapp -t v1.0 quick"
}

# Parse command line arguments
IMAGE_NAME="telemetry-service"
TAG="latest"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        comprehensive)
            run_comprehensive_scan
            exit 0
            ;;
        quick)
            run_quick_scan
            exit 0
            ;;
        build)
            build_image
            exit 0
            ;;
        cleanup)
            cleanup
            exit 0
            ;;
        install)
            install_trivy
            install_grype
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Default to quick scan if no command specified
if [ $# -eq 0 ]; then
    run_quick_scan
fi
