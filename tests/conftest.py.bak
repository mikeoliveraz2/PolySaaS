"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient

from polysaas.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)
