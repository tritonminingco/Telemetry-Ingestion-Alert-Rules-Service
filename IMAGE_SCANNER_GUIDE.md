# Image Scanner Integration Guide

This guide covers the comprehensive image scanning integration using Trivy and Grype vulnerability scanners, ensuring all pipelines run green with robust security validation.

## 🎯 Overview

The image scanner integration provides:
- **Multi-tool scanning**: Trivy and Grype for comprehensive coverage
- **Multiple scan types**: Filesystem, configuration, secrets, and image scanning
- **CI/CD integration**: Automated scanning in GitHub Actions
- **Local development**: Command-line tools for local testing
- **Multiple output formats**: Table, JSON, and SARIF for different use cases

## 🛠️ Tools Integrated

### 1. Trivy (Aqua Security)
- **Purpose**: Comprehensive vulnerability scanner
- **Capabilities**:
  - Filesystem scanning (OS packages, language dependencies)
  - Configuration scanning (Docker, Kubernetes, Terraform)
  - Secret scanning (API keys, passwords, tokens)
  - Image scanning (container vulnerabilities)
- **Output formats**: Table, JSON, SARIF
- **Severity levels**: CRITICAL, HIGH, MEDIUM, LOW

### 2. Grype (Anchore)
- **Purpose**: Container image vulnerability scanner
- **Capabilities**:
  - OS package vulnerability scanning
  - Language dependency scanning
  - Comprehensive vulnerability database
- **Output formats**: Table, JSON, CycloneDX
- **Integration**: GitHub Actions and local CLI

### 3. Snyk (Optional)
- **Purpose**: Additional container security scanning
- **Requirements**: SNYK_TOKEN secret in GitHub
- **Capabilities**: Advanced vulnerability detection and remediation

## 📁 File Structure

```
.github/workflows/
├── ci.yml                    # Main CI pipeline with enhanced scanning
├── docker-build.yml          # Docker build with comprehensive scanning
└── docker-hub-push.yml       # Docker Hub push pipeline

scripts/
└── image-scan.sh            # Local image scanning script

docs/
└── IMAGE_SCANNER_GUIDE.md   # This documentation
```

## 🚀 Quick Start

### 1. Local Development

```bash
# Install scanning tools
./scripts/image-scan.sh install

# Run quick scan
./scripts/image-scan.sh quick

# Run comprehensive scan
./scripts/image-scan.sh comprehensive

# Build image only
./scripts/image-scan.sh build

# Clean up scan files
./scripts/image-scan.sh cleanup
```

### 2. CI/CD Pipeline

The scanning is automatically integrated into GitHub Actions:

```yaml
# Triggers on push/PR to main/develop
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
```

## 🔧 Configuration

### Environment Variables

```bash
# GitHub Secrets (for Snyk integration)
SNYK_TOKEN=your_snyk_token_here

# Local configuration
IMAGE_NAME=telemetry-service
TAG=latest
```

### Scan Configuration

#### Trivy Configuration
```yaml
# Scan types
- fs: Filesystem vulnerabilities
- config: Configuration issues
- secret: Secret detection
- image: Container image vulnerabilities

# Severity levels
- CRITICAL: Immediate action required
- HIGH: High priority fixes needed
- MEDIUM: Medium priority issues
- LOW: Low priority findings
```

#### Grype Configuration
```yaml
# Output formats
- table: Human-readable output
- json: Machine-readable JSON
- cyclonedx: SBOM format

# Severity filtering
- fail-build: false (don't fail pipeline on findings)
```

## 📊 Scan Results

### Output Files

```
trivy-fs-results.table      # Filesystem scan results
trivy-config-results.table  # Configuration scan results
trivy-secret-results.table  # Secret scan results
trivy-image-results.table   # Image scan results
grype-results.table         # Grype scan results
*.sarif                     # SARIF format for GitHub Security tab
*.json                      # JSON format for automation
```

### GitHub Security Tab Integration

All scan results are automatically uploaded to GitHub Security tab:
- **Vulnerability alerts**: Automatic creation for new findings
- **SARIF integration**: Structured results for better visibility
- **Severity filtering**: Configurable thresholds for pipeline failure

## 🔍 Scan Types Explained

### 1. Filesystem Scanning (Trivy fs)
**Purpose**: Scan application code and dependencies for vulnerabilities

**What it scans**:
- OS packages (apt, yum, apk)
- Language dependencies (pip, npm, maven)
- Application code vulnerabilities

**Example output**:
```
VulnerabilityID  PackageName  InstalledVersion  FixedVersion  Severity
CVE-2023-1234   openssl      1.1.1f-1ubuntu2   1.1.1f-1ubuntu3  HIGH
```

### 2. Configuration Scanning (Trivy config)
**Purpose**: Scan infrastructure configuration for security issues

**What it scans**:
- Dockerfile security best practices
- Kubernetes manifests
- Terraform configurations
- Infrastructure as Code

**Example output**:
```
MisconfigurationID  Type      Severity  Title
Dockerfile.001      Dockerfile  HIGH     Root user detected
```

### 3. Secret Scanning (Trivy secret)
**Purpose**: Detect accidentally committed secrets

**What it scans**:
- API keys
- Passwords
- Tokens
- Private keys

**Example output**:
```
SecretID  Category  Severity  Title
aws-key   AWS       HIGH      AWS Access Key ID
```

### 4. Image Scanning (Trivy image)
**Purpose**: Scan built container images for vulnerabilities

**What it scans**:
- Base image vulnerabilities
- Installed packages
- Runtime dependencies

**Example output**:
```
VulnerabilityID  PackageName  InstalledVersion  FixedVersion  Severity
CVE-2023-5678   python       3.11.0            3.11.1        MEDIUM
```

## 🚨 Pipeline Validation

### Success Criteria

For pipelines to run green, ensure:

1. **No CRITICAL vulnerabilities** in any scan type
2. **No HIGH vulnerabilities** in production images
3. **All scan tools complete successfully**
4. **Results uploaded to GitHub Security tab**

### Failure Conditions

Pipelines will fail if:
- CRITICAL vulnerabilities detected
- Scan tools fail to execute
- Required secrets missing (for Snyk)

### Bypass Options

For development/testing:
```yaml
# In workflow files
fail-build: false  # Don't fail on findings
severity: CRITICAL,HIGH  # Only fail on critical/high
```

## 🛡️ Security Best Practices

### 1. Regular Scanning
- **Daily**: Automated CI/CD scanning
- **Weekly**: Manual comprehensive scans
- **Monthly**: Security review of findings

### 2. Vulnerability Management
- **Immediate**: Fix CRITICAL vulnerabilities
- **Within 7 days**: Fix HIGH vulnerabilities
- **Within 30 days**: Fix MEDIUM vulnerabilities
- **Document**: LOW vulnerabilities with risk assessment

### 3. Base Image Security
- Use minimal base images
- Regular base image updates
- Multi-stage builds for smaller attack surface

### 4. Dependency Management
- Regular dependency updates
- Automated vulnerability scanning
- Pinning dependency versions

## 🔧 Troubleshooting

### Common Issues

#### 1. Trivy Installation Fails
```bash
# Manual installation
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.48.0
```

#### 2. Grype Installation Fails
```bash
# Manual installation
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
```

#### 3. Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### 4. Scan Timeout
```bash
# Increase timeout in workflows
timeout-minutes: 30
```

### Debug Commands

```bash
# Check tool versions
trivy --version
grype --version

# Test individual scans
trivy fs --severity HIGH .
trivy image --severity HIGH telemetry-service:latest
grype telemetry-service:latest

# Check scan results
ls -la trivy-*-results.* grype-results.*
```

## 📈 Monitoring and Reporting

### GitHub Security Tab
- Automatic vulnerability alerts
- Historical scan data
- Severity-based filtering

### Custom Reporting
```bash
# Generate JSON reports
./scripts/image-scan.sh comprehensive

# Parse results for automation
jq '.Results[].Vulnerabilities[] | select(.Severity == "CRITICAL")' trivy-fs-results.json
```

### Integration with Security Tools
- **DefectDojo**: Import SARIF results
- **Jira**: Create tickets for vulnerabilities
- **Slack**: Notify team of critical findings

## 🔄 Continuous Improvement

### 1. Regular Updates
- Update scanning tools monthly
- Review and update scan configurations
- Monitor new vulnerability databases

### 2. Performance Optimization
- Use scan caching in CI/CD
- Optimize scan frequency
- Parallel scanning where possible

### 3. Coverage Expansion
- Add new scan types as needed
- Integrate additional security tools
- Custom scan rules for project-specific needs

## 📚 Additional Resources

- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Grype Documentation](https://github.com/anchore/grype)
- [GitHub Security Features](https://docs.github.com/en/code-security)
- [SARIF Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)

## ✅ Validation Checklist

- [ ] Trivy installed and working
- [ ] Grype installed and working
- [ ] Local scanning script functional
- [ ] CI/CD pipelines integrated
- [ ] GitHub Security tab integration working
- [ ] All pipelines running green
- [ ] Documentation complete
- [ ] Team trained on usage

---

**Note**: This integration ensures comprehensive security scanning while maintaining pipeline efficiency. Regular updates and monitoring are essential for maintaining security posture.
