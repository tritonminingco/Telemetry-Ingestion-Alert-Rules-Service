# Branch Protection Guide

This guide explains the branch protection setup for the DSG Telemetry Service repository and how to configure and use it.

## Overview

Branch protection ensures code quality and security by enforcing specific rules before code can be merged into protected branches. This setup includes:

- **CI/CD Pipeline**: Automated testing, linting, and security checks
- **Code Reviews**: Required approvals from team members
- **Code Owners**: Automatic review requests for specific file types
- **Security Scanning**: Vulnerability detection and dependency analysis
- **Deployment Automation**: Safe deployment to production

## Protected Branches

### Main Branch (`main`)
- **Purpose**: Production-ready code
- **Protection Level**: Maximum security
- **Requirements**:
  - 2 approving reviews required
  - Code owner reviews required
  - All CI checks must pass
  - Linear history enforced
  - No direct pushes allowed
  - Admin restrictions enforced

### Develop Branch (`develop`)
- **Purpose**: Integration and testing
- **Protection Level**: Moderate security
- **Requirements**:
  - 1 approving review required
  - All CI checks must pass
  - No direct pushes allowed
  - Conversation resolution required

## CI/CD Pipeline

The CI/CD pipeline runs the following checks:

### 1. Testing (`test` job)
- **Python Tests**: Unit and integration tests with pytest
- **Code Coverage**: Minimum coverage reporting
- **Database Tests**: PostgreSQL integration tests
- **Redis Tests**: Cache and session tests

### 2. Code Quality (`linting` step)
- **Black**: Code formatting check
- **isort**: Import sorting check
- **flake8**: Style and complexity checks

### 3. Security (`security-scan` job)
- **Bandit**: Python security linting
- **Safety**: Dependency vulnerability scanning
- **Trivy**: Container vulnerability scanning

### 4. Docker Build (`docker-build` job)
- **Image Build**: Docker image creation test
- **Image Validation**: Basic functionality test

## Setup Instructions

### Prerequisites

1. **GitHub CLI**: Install and authenticate
   ```bash
   # Install GitHub CLI
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh

   # Authenticate
   gh auth login
   ```

2. **Repository Access**: Ensure you have admin access to the repository

### Automated Setup

Run the automated setup script:

```bash
./scripts/setup-branch-protection.sh
```

This script will:
- Create the `develop` branch if it doesn't exist
- Set up protection rules for both `main` and `develop` branches
- Configure all required status checks and review requirements

### Manual Setup

If you prefer to set up branch protection manually:

1. **Go to Repository Settings**:
   - Navigate to your repository on GitHub
   - Go to Settings → Branches

2. **Add Branch Protection Rule for `main`**:
   - Click "Add rule"
   - Branch name pattern: `main`
   - Enable "Require a pull request before merging"
   - Set "Required approving reviews" to 2
   - Enable "Require review from code owners"
   - Enable "Dismiss stale pull request approvals when new commits are pushed"
   - Enable "Require review from code owners"
   - Enable "Require last push approval"
   - Enable "Require status checks to pass before merging"
   - Add status checks: `test`, `docker-build`, `security-scan`
   - Enable "Require branches to be up to date before merging"
   - Enable "Require linear history"
   - Enable "Require conversation resolution before merging"
   - Enable "Restrict pushes that create files"
   - Enable "Do not allow bypassing the above settings"

3. **Add Branch Protection Rule for `develop`**:
   - Click "Add rule"
   - Branch name pattern: `develop`
   - Enable "Require a pull request before merging"
   - Set "Required approving reviews" to 1
   - Enable "Dismiss stale pull request approvals when new commits are pushed"
   - Enable "Require status checks to pass before merging"
   - Add status checks: `test`, `docker-build`, `security-scan`
   - Enable "Require branches to be up to date before merging"
   - Enable "Require conversation resolution before merging"

## Code Owners

The `.github/CODEOWNERS` file defines who is responsible for reviewing different parts of the codebase:

- **@team-leads**: Python code, tests, documentation, dependencies
- **@devops-team**: Infrastructure, Docker, CI/CD configuration

### Adding Code Owners

To add new code owners:

1. Edit `.github/CODEOWNERS`
2. Add the appropriate patterns and usernames/team names
3. Create a pull request to update the file

## Workflow

### Development Workflow

1. **Create Feature Branch**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Test**:
   ```bash
   # Make your changes
   # Run tests locally
   pytest tests/
   # Run linting
   black .
   isort .
   flake8 .
   ```

3. **Push and Create Pull Request**:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**:
   - Target: `develop` branch
   - Fill out the PR template
   - Request reviews from appropriate team members

### Release Workflow

1. **Create Release Branch**:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v1.0.0
   ```

2. **Prepare Release**:
   - Update version numbers
   - Update changelog
   - Test thoroughly

3. **Merge to Main**:
   - Create PR from `release/v1.0.0` to `main`
   - Requires 2 approvals and code owner reviews
   - All CI checks must pass

4. **Deploy**:
   - Automatic deployment triggers after successful merge to `main`
   - Monitor deployment status

## Troubleshooting

### Common Issues

1. **CI Checks Failing**:
   - Check the GitHub Actions tab for detailed error messages
   - Run tests locally to reproduce issues
   - Fix issues and push new commits

2. **Review Requirements Not Met**:
   - Ensure you have the required number of approvals
   - Check that code owners have approved (if required)
   - Verify all conversations are resolved

3. **Branch Protection Blocking Merges**:
   - Ensure your branch is up to date with the target branch
   - Check that all required status checks are passing
   - Verify that all review requirements are satisfied

### Getting Help

- **CI/CD Issues**: Contact the DevOps team
- **Code Review Issues**: Contact team leads
- **Security Issues**: Contact the security team

## Security Considerations

- **Secrets**: Never commit secrets to the repository
- **Dependencies**: Regularly update dependencies to patch vulnerabilities
- **Access Control**: Review and update team access regularly
- **Audit Logs**: Monitor repository activity for suspicious behavior

## Best Practices

1. **Small, Focused PRs**: Keep pull requests small and focused on a single feature or fix
2. **Clear Commit Messages**: Use conventional commit format
3. **Comprehensive Testing**: Write tests for new features and bug fixes
4. **Documentation**: Update documentation when adding new features
5. **Security First**: Always consider security implications of changes
6. **Code Review**: Provide constructive feedback during code reviews

## Monitoring and Maintenance

### Regular Tasks

- **Weekly**: Review and update dependencies
- **Monthly**: Review branch protection rules
- **Quarterly**: Review and update code owners
- **Annually**: Review and update CI/CD pipeline

### Metrics to Track

- **PR Review Time**: Average time to get PR reviews
- **CI Failure Rate**: Percentage of CI runs that fail
- **Deployment Success Rate**: Percentage of successful deployments
- **Security Issues**: Number of security vulnerabilities found

## Support

For questions or issues with branch protection:

1. Check this documentation first
2. Review GitHub's branch protection documentation
3. Contact the DevOps team for technical issues
4. Contact team leads for process questions
