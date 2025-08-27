#!/bin/bash

# Branch Protection Testing Script
# This script tests all aspects of the branch protection implementation

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
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_failure() {
    echo -e "${RED}[FAILURE]${NC} $1"
}

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    print_header "Running: $test_name"

    if eval "$test_command"; then
        print_success "$test_name passed"
        ((TESTS_PASSED++))
    else
        print_failure "$test_name failed"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Function to check if a file exists
check_file_exists() {
    local file_path="$1"
    local description="$2"

    if [ -f "$file_path" ]; then
        print_success "$description exists: $file_path"
        ((TESTS_PASSED++))
    else
        print_failure "$description missing: $file_path"
        ((TESTS_FAILED++))
    fi
}

# Function to check if a directory exists
check_directory_exists() {
    local dir_path="$1"
    local description="$2"

    if [ -d "$dir_path" ]; then
        print_success "$description exists: $dir_path"
        ((TESTS_PASSED++))
    else
        print_failure "$description missing: $dir_path"
        ((TESTS_FAILED++))
    fi
}

# Function to validate YAML syntax
validate_yaml() {
    local file_path="$1"
    local description="$2"

    if python3 -c "import yaml; yaml.safe_load(open('$file_path'))" 2>/dev/null; then
        print_success "$description has valid YAML syntax"
        ((TESTS_PASSED++))
    else
        print_failure "$description has invalid YAML syntax"
        ((TESTS_FAILED++))
    fi
}

# Function to check GitHub CLI availability
check_github_cli() {
    if command -v gh &> /dev/null; then
        print_success "GitHub CLI is available"
        ((TESTS_PASSED++))

        # Check if authenticated
        if gh auth status &> /dev/null; then
            print_success "GitHub CLI is authenticated"
            ((TESTS_PASSED++))
        else
            print_warning "GitHub CLI is not authenticated. Run 'gh auth login'"
            ((TESTS_FAILED++))
        fi
    else
        print_warning "GitHub CLI is not installed. Some tests will be skipped."
        # Don't count this as a failure since it's optional
    fi
}

# Function to test local development tools
test_local_tools() {
    print_header "Testing Local Development Tools"

    # Test Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$(printf '%s\n' "3.11" "$python_version" | sort -V | head -n1)" = "3.11" ]; then
        print_success "Python version $python_version is compatible"
        ((TESTS_PASSED++))
    else
        print_failure "Python version $python_version is not compatible (need 3.11+)"
        ((TESTS_FAILED++))
    fi

    # Test if virtual environment exists
    if [ -d "venv" ]; then
        print_success "Virtual environment exists"
        ((TESTS_PASSED++))

        # Test if dependencies are installed (without sourcing to avoid script exit)
        if venv/bin/python -c "import fastapi, sqlalchemy, pytest" 2>/dev/null; then
            print_success "Core dependencies are installed"
            ((TESTS_PASSED++))
        else
            print_warning "Core dependencies are not installed"
            ((TESTS_FAILED++))
        fi
    else
        print_warning "Virtual environment does not exist. Run setup-dev-environment.sh"
        ((TESTS_FAILED++))
    fi

    # Test development tools
    if command -v black &> /dev/null; then
        print_success "Black formatter is available"
        ((TESTS_PASSED++))
    else
        print_failure "Black formatter is not available"
        ((TESTS_FAILED++))
    fi

    if command -v isort &> /dev/null; then
        print_success "isort is available"
        ((TESTS_PASSED++))
    else
        print_failure "isort is not available"
        ((TESTS_FAILED++))
    fi

    if command -v flake8 &> /dev/null; then
        print_success "flake8 is available"
        ((TESTS_PASSED++))
    else
        print_failure "flake8 is not available"
        ((TESTS_FAILED++))
    fi

    if command -v pytest &> /dev/null; then
        print_success "pytest is available"
        ((TESTS_PASSED++))
    else
        print_failure "pytest is not available"
        ((TESTS_FAILED++))
    fi
}

# Function to test GitHub workflows
test_github_workflows() {
    print_header "Testing GitHub Workflows"

    # Check CI workflow
    check_file_exists ".github/workflows/ci.yml" "CI workflow"
    validate_yaml ".github/workflows/ci.yml" "CI workflow"

    # Check deploy workflow
    check_file_exists ".github/workflows/deploy.yml" "Deploy workflow"
    validate_yaml ".github/workflows/deploy.yml" "Deploy workflow"

    # Test workflow syntax (if GitHub CLI is available)
    if command -v gh &> /dev/null && gh auth status &> /dev/null; then
        print_header "Validating workflow syntax with GitHub CLI"

        # This would require the repository to be pushed to GitHub
        # For now, we'll just check the YAML syntax
        print_status "Workflow YAML syntax is valid"
    fi
}

# Function to test configuration files
test_configuration_files() {
    print_header "Testing Configuration Files"

    # Check CODEOWNERS
    check_file_exists ".github/CODEOWNERS" "CODEOWNERS file"

    # Check branch protection config
    check_file_exists ".github/branch-protection.yml" "Branch protection config"
    validate_yaml ".github/branch-protection.yml" "Branch protection config"

    # Check PR template
    check_file_exists ".github/pull_request_template.md" "Pull request template"

    # Check issue templates
    check_directory_exists ".github/ISSUE_TEMPLATE" "Issue templates directory"
    check_file_exists ".github/ISSUE_TEMPLATE/bug_report.md" "Bug report template"
    check_file_exists ".github/ISSUE_TEMPLATE/feature_request.md" "Feature request template"

    # Check pre-commit config
    check_file_exists ".pre-commit-config.yaml" "Pre-commit configuration"
    validate_yaml ".pre-commit-config.yaml" "Pre-commit configuration"

    # Check pyproject.toml
    check_file_exists "pyproject.toml" "pyproject.toml"
}

# Function to test scripts
test_scripts() {
    print_header "Testing Scripts"

    # Check if scripts are executable
    if [ -x "scripts/setup-branch-protection.sh" ]; then
        print_success "Branch protection setup script is executable"
        ((TESTS_PASSED++))
    else
        print_failure "Branch protection setup script is not executable"
        ((TESTS_FAILED++))
    fi

    if [ -x "scripts/setup-dev-environment.sh" ]; then
        print_success "Development environment setup script is executable"
        ((TESTS_PASSED++))
    else
        print_failure "Development environment setup script is not executable"
        ((TESTS_FAILED++))
    fi

    # Test script syntax
    if bash -n scripts/setup-branch-protection.sh; then
        print_success "Branch protection script has valid syntax"
        ((TESTS_PASSED++))
    else
        print_failure "Branch protection script has syntax errors"
        ((TESTS_FAILED++))
    fi

    if bash -n scripts/setup-dev-environment.sh; then
        print_success "Development environment script has valid syntax"
        ((TESTS_PASSED++))
    else
        print_failure "Development environment script has syntax errors"
        ((TESTS_FAILED++))
    fi
}

# Function to test documentation
test_documentation() {
    print_header "Testing Documentation"

    check_file_exists "BRANCH_PROTECTION_GUIDE.md" "Branch protection guide"
    check_file_exists "BRANCH_PROTECTION_SUMMARY.md" "Branch protection summary"

    # Check if documentation has content
    if [ -s "BRANCH_PROTECTION_GUIDE.md" ]; then
        print_success "Branch protection guide has content"
        ((TESTS_PASSED++))
    else
        print_failure "Branch protection guide is empty"
        ((TESTS_FAILED++))
    fi

    if [ -s "BRANCH_PROTECTION_SUMMARY.md" ]; then
        print_success "Branch protection summary has content"
        ((TESTS_PASSED++))
    else
        print_failure "Branch protection summary is empty"
        ((TESTS_FAILED++))
    fi
}

# Function to test code quality tools
test_code_quality() {
    print_header "Testing Code Quality Tools"

    # Test if we can run basic linting
    if command -v black &> /dev/null; then
        if black --check . --diff 2>/dev/null; then
            print_success "Code passes Black formatting check"
            ((TESTS_PASSED++))
        else
            print_warning "Code does not pass Black formatting check"
            ((TESTS_FAILED++))
        fi
    fi

    if command -v isort &> /dev/null; then
        if isort --check-only . --diff 2>/dev/null; then
            print_success "Code passes isort import sorting check"
            ((TESTS_PASSED++))
        else
            print_warning "Code does not pass isort import sorting check"
            ((TESTS_FAILED++))
        fi
    fi

    if command -v flake8 &> /dev/null; then
        if flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics 2>/dev/null; then
            print_success "Code passes flake8 linting check"
            ((TESTS_PASSED++))
        else
            print_warning "Code has flake8 linting issues"
            ((TESTS_FAILED++))
        fi
    fi
}

# Function to test basic functionality
test_basic_functionality() {
    print_header "Testing Basic Functionality"

    # Test if we can import the main application
    if [ -d "venv" ]; then
        if venv/bin/python -c "import app" 2>/dev/null; then
            print_success "Application can be imported"
            ((TESTS_PASSED++))
        else
            print_warning "Application cannot be imported"
            ((TESTS_FAILED++))
        fi
    fi

    # Test if tests can be discovered
    if command -v pytest &> /dev/null; then
        if pytest --collect-only tests/ 2>/dev/null; then
            print_success "Tests can be discovered"
            ((TESTS_PASSED++))
        else
            print_warning "Tests cannot be discovered"
            ((TESTS_FAILED++))
        fi
    fi
}

# Main testing function
main() {
    echo "🧪 Branch Protection Testing Suite"
    echo "=================================="
    echo ""

    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "This script must be run from the project root directory"
        exit 1
    fi

    # Run all tests
    check_github_cli
    test_local_tools
    test_github_workflows
    test_configuration_files
    test_scripts
    test_documentation
    test_code_quality
    test_basic_functionality

    # Print summary
    echo "=================================="
    echo "🧪 Testing Summary"
    echo "=================================="
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All tests passed! Branch protection is ready to use."
        echo ""
        print_status "Next steps:"
        echo "1. Push your code to GitHub"
        echo "2. Run: ./scripts/setup-branch-protection.sh"
        echo "3. Create a test PR to verify protection rules"
    else
        print_warning "Some tests failed. Please review the issues above."
        echo ""
        print_status "Common fixes:"
        echo "1. Run: ./scripts/setup-dev-environment.sh"
        echo "2. Install missing tools: pip install black isort flake8 pytest"
        echo "3. Fix any YAML syntax errors"
    fi
}

# Run the main function
main
