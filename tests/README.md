# PolySaaS Tests

This directory will contain tests for the PolySaaS application.

## Planned Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration and fixtures
├── unit/                # Unit tests
│   ├── __init__.py
│   ├── test_user_service.py
│   ├── test_tenant_service.py
│   └── test_utils.py
├── integration/         # Integration tests
│   ├── __init__.py
│   ├── test_api.py
│   └── test_database.py
└── e2e/                 # End-to-end tests
    ├── __init__.py
    └── test_user_flow.py
```

## Test Types

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution
- High coverage

### Integration Tests
- Test component interactions
- Use test database
- Test API endpoints
- Verify data flow

### End-to-End Tests
- Test complete user workflows
- Use real or staging environment
- Simulate user actions
- Verify business processes

## Running Tests

Once implemented, tests can be run with:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_user_service.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests  
pytest tests/integration/

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_user_service.py::test_create_user
```

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --strict-markers
    -ra
markers =
    slow: marks tests as slow
    integration: marks integration tests
    e2e: marks end-to-end tests
```

### conftest.py Example

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.polysaas.db.base import Base

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create database session for tests"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client():
    """Create test client"""
    from src.polysaas.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)
```

## Best Practices

1. **AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Keep tests focused
3. **Descriptive Names**: Use clear test function names
4. **Use Fixtures**: Reuse common setup code
5. **Mock External Services**: Don't call real APIs
6. **Test Edge Cases**: Not just happy paths
7. **Keep Tests Fast**: Run quickly for rapid feedback
8. **Test Behavior**: Not implementation details

## Example Test

```python
def test_create_user_with_valid_data(db_session):
    """
    Test that a user can be created with valid data.
    
    Given: Valid user data
    When: create_user is called
    Then: User is created successfully
    """
    # Arrange
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123"
    }
    service = UserService(db_session)
    
    # Act
    user = service.create_user(**user_data)
    
    # Assert
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.password != user_data["password"]  # Should be hashed
```

## Coverage Goals

- **Overall**: 80%+ coverage
- **Critical Paths**: 100% coverage
- **New Code**: 90%+ coverage
- **Public APIs**: 100% coverage

## Continuous Integration

Tests run automatically on:
- Every pull request
- Commits to develop/staging/main
- Before deployment

## Status

**Status**: Planned - Not yet implemented

Tests will be added when the FastAPI application is implemented.

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test-Driven Development](https://testdriven.io/)
