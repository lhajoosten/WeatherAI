import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


def test_health_endpoint():
    """Test health endpoint returns expected response."""
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Status can be "healthy" or "degraded" depending on service availability
    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "openai" in data["services"]


def test_root_endpoint():
    """Test root endpoint returns basic info."""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "WeatherAI Backend API"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"


@pytest.mark.asyncio
async def test_health_endpoint_async():
    """Test health endpoint with async client."""
    from fastapi.testclient import TestClient
    
    # Use TestClient for async tests in this context
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    # Status can be "healthy" or "degraded" depending on service availability
    assert data["status"] in ["healthy", "degraded"]
