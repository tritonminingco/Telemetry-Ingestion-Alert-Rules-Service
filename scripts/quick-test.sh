#!/bin/bash

echo "🧪 Quick Branch Protection Test"
echo "================================"

# Test 1: Check if all required files exist
echo ""
echo "📁 Checking required files..."

files=(
    ".github/workflows/ci.yml"
    ".github/workflows/deploy.yml"
    ".github/CODEOWNERS"
    ".github/branch-protection.yml"
    ".github/pull_request_template.md"
    ".github/ISSUE_TEMPLATE/bug_report.md"
    ".github/ISSUE_TEMPLATE/feature_request.md"
    ".pre-commit-config.yaml"
    "pyproject.toml"
    "scripts/setup-branch-protection.sh"
    "scripts/setup-dev-environment.sh"
    "BRANCH_PROTECTION_GUIDE.md"
    "BRANCH_PROTECTION_SUMMARY.md"
)

all_files_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
        all_files_exist=false
    fi
done

# Test 2: Check if scripts are executable
echo ""
echo "🔧 Checking script permissions..."

scripts=(
    "scripts/setup-branch-protection.sh"
    "scripts/setup-dev-environment.sh"
)

all_scripts_executable=true
for script in "${scripts[@]}"; do
    if [ -x "$script" ]; then
        echo "✅ $script (executable)"
    else
        echo "❌ $script (not executable)"
        all_scripts_executable=false
    fi
done

# Test 3: Validate YAML files
echo ""
echo "📋 Validating YAML files..."

yaml_files=(
    ".github/workflows/ci.yml"
    ".github/workflows/deploy.yml"
    ".github/branch-protection.yml"
    ".pre-commit-config.yaml"
)

all_yaml_valid=true
for yaml_file in "${yaml_files[@]}"; do
    if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
        echo "✅ $yaml_file (valid YAML)"
    else
        echo "❌ $yaml_file (invalid YAML)"
        all_yaml_valid=false
    fi
done

# Test 4: Check Python environment
echo ""
echo "🐍 Checking Python environment..."

if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "✅ Python $python_version available"
else
    echo "❌ Python3 not available"
fi

if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "⚠️  Virtual environment does not exist"
fi

# Test 5: Check development tools
echo ""
echo "🛠️  Checking development tools..."

tools=("black" "isort" "flake8" "pytest")
for tool in "${tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo "✅ $tool available"
    else
        echo "⚠️  $tool not available"
    fi
done

# Test 6: Check GitHub CLI
echo ""
echo "🔗 Checking GitHub CLI..."

if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI available"
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI authenticated"
    else
        echo "⚠️  GitHub CLI not authenticated"
    fi
else
    echo "⚠️  GitHub CLI not installed"
fi

# Summary
echo ""
echo "================================"
echo "📊 Test Summary"
echo "================================"

if [ "$all_files_exist" = true ]; then
    echo "✅ All required files exist"
else
    echo "❌ Some required files are missing"
fi

if [ "$all_scripts_executable" = true ]; then
    echo "✅ All scripts are executable"
else
    echo "❌ Some scripts are not executable"
fi

if [ "$all_yaml_valid" = true ]; then
    echo "✅ All YAML files are valid"
else
    echo "❌ Some YAML files are invalid"
fi

echo ""
echo "🎯 Branch Protection Status:"
if [ "$all_files_exist" = true ] && [ "$all_scripts_executable" = true ] && [ "$all_yaml_valid" = true ]; then
    echo "✅ READY TO USE!"
    echo ""
    echo "Next steps:"
    echo "1. Push code to GitHub"
    echo "2. Run: ./scripts/setup-branch-protection.sh"
    echo "3. Create a test PR to verify protection rules"
else
    echo "⚠️  NEEDS ATTENTION"
    echo ""
    echo "Please fix the issues above before proceeding."
fi
