# Contributing to PolySaaS

Thank you for your interest in contributing to PolySaaS! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Trolling, insulting, or derogatory comments
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

- Git
- Python 3.8+
- Node.js 14+ (for WordPress tooling)
- Docker (optional, for containerized development)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/PolySaaS.git
cd PolySaaS
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/mikeoliveraz2/PolySaaS.git
```

### Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your local main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write code
- Add tests
- Update documentation
- Follow coding standards

### 3. Test Your Changes

```bash
# Run tests
pytest

# Run linting
flake8 src/
black src/ --check

# Run type checking
mypy src/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Maximum line length: 88 characters (Black default)
- Use docstrings for classes and public methods

Example:
```python
def calculate_total(items: List[Item], tax_rate: float = 0.1) -> Decimal:
    """
    Calculate total price including tax.
    
    Args:
        items: List of items to calculate total for
        tax_rate: Tax rate as decimal (default: 0.1 for 10%)
        
    Returns:
        Total price including tax
        
    Raises:
        ValueError: If tax_rate is negative
    """
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    
    subtotal = sum(item.price for item in items)
    return subtotal * (1 + tax_rate)
```

### JavaScript/TypeScript

- Follow Airbnb Style Guide
- Use ES6+ features
- Prefer `const` over `let`, avoid `var`
- Use meaningful variable names
- Add JSDoc comments for functions

### PHP (WordPress)

- Follow WordPress Coding Standards
- Use WordPress functions where available
- Sanitize all inputs
- Escape all outputs
- Use prepared statements for database queries

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/).

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no code change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(auth): add JWT authentication

Implement JWT-based authentication system with refresh tokens.
Includes middleware for protecting routes.

Closes #123
```

```
fix(api): resolve user deletion error

Fixed issue where deleting a user would fail if they had
associated orders. Now properly handles cascade deletion.

Fixes #456
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)
- [ ] No sensitive data in code
- [ ] Commits follow convention

### PR Description

Include:
1. **What**: Description of changes
2. **Why**: Reason for changes
3. **How**: Implementation approach
4. **Testing**: How to test the changes
5. **Screenshots**: For UI changes
6. **Related Issues**: Link to related issues

### Example PR Template

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why this change is needed.

## Changes
- Change 1
- Change 2
- Change 3

## Testing
How to test these changes:
1. Step 1
2. Step 2
3. Expected result

## Screenshots
(if applicable)

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] No breaking changes (or documented)

## Related Issues
Closes #123
Related to #456
```

### Review Process

1. Automated checks run (CI/CD)
2. Code review by maintainers
3. Address feedback
4. Approval required before merge
5. Squash and merge to main

## Testing

### Writing Tests

```python
# tests/test_user_service.py
import pytest
from src.polysaas.services.user_service import UserService

def test_create_user():
    """Test user creation with valid data"""
    service = UserService()
    user = service.create_user(
        email="test@example.com",
        password="SecurePass123"
    )
    assert user.email == "test@example.com"
    assert user.id is not None

def test_create_user_invalid_email():
    """Test user creation with invalid email"""
    service = UserService()
    with pytest.raises(ValueError):
        service.create_user(
            email="invalid-email",
            password="SecurePass123"
        )
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_user_service.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Test Coverage

- Aim for 80%+ coverage
- All public APIs must have tests
- Critical paths must be tested
- Edge cases should be covered

## Documentation

### Code Documentation

- Use docstrings for all public functions/classes
- Keep comments clear and concise
- Update README when adding features
- Document breaking changes

### API Documentation

- Document all endpoints
- Include request/response examples
- Note authentication requirements
- List possible error codes

### User Documentation

- Write clear, step-by-step guides
- Include screenshots where helpful
- Keep language simple and accessible
- Test instructions with fresh eyes

## Questions?

- Open an issue for bugs or feature requests
- Join our discussion forum for questions
- Check existing issues and PRs first
- Be patient and respectful

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- README.md (contributors section)
- Release notes

Thank you for contributing to PolySaaS!
