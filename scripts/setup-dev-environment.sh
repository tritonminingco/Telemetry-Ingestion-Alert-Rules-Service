#!/bin/bash

# Development Environment Setup Script
# This script sets up the local development environment with all necessary tools

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
    echo -e "${BLUE}[SETUP]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

print_header "Setting up DSG Telemetry Service development environment..."

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi

print_status "✅ Python version $python_version is compatible"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_status "✅ Virtual environment created"
else
    print_status "✅ Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_status "Installing project dependencies..."
pip install -r requirements.txt

# Install development dependencies
print_status "Installing development dependencies..."
pip install -e ".[dev]"

# Install pre-commit hooks
print_status "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Check if Docker is available
if command -v docker &> /dev/null; then
    print_status "✅ Docker is available"
else
    print_warning "Docker is not installed. Some features may not work."
    print_status "Install Docker: https://docs.docker.com/get-docker/"
fi

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    print_status "✅ GitHub CLI is available"
else
    print_warning "GitHub CLI is not installed. Branch protection setup will not work."
    print_status "Install GitHub CLI: https://cli.github.com/"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    cp env.example .env
    print_warning "Please edit .env file with your configuration"
else
    print_status "✅ .env file already exists"
fi

# Run initial tests to verify setup
print_status "Running initial tests to verify setup..."
if pytest tests/ -v --tb=short; then
    print_status "✅ Tests passed - setup is working correctly"
else
    print_warning "Some tests failed. This might be expected if database is not configured."
fi

# Run linting to check code quality
print_status "Running code quality checks..."
if black --check . && isort --check-only . && flake8 .; then
    print_status "✅ Code quality checks passed"
else
    print_warning "Code quality checks failed. Run 'black .' and 'isort .' to fix formatting."
fi

print_header "Development environment setup completed!"

echo ""
print_status "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Set up your database (PostgreSQL + Redis)"
echo "3. Run 'alembic upgrade head' to set up database schema"
echo "4. Run 'python -m app.scripts.seed' to seed initial data"
echo "5. Start the service with 'uvicorn app.main:app --reload'"
echo ""
print_status "Useful commands:"
echo "- Run tests: pytest tests/"
echo "- Format code: black ."
echo "- Sort imports: isort ."
echo "- Lint code: flake8 ."
echo "- Security check: bandit -r app/"
echo "- Type check: mypy app/"
echo ""
print_status "For branch protection setup:"
echo "- Install GitHub CLI: https://cli.github.com/"
echo "- Run: ./scripts/setup-branch-protection.sh"
echo ""
print_status "Happy coding! 🚀"
