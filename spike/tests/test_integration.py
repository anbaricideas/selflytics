"""Integration test for spike validation."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from spike.main import app


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="function")
async def client():
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def test_health_check(client):
    """Test health endpoint returns expected status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "selflytics-spike"


@pytest.mark.skip(
    reason="TestModel provides invalid args to tools (e.g., 'a' for dates). "
    "Real API testing requires OPENAI_API_KEY to be set."
)
async def test_chat_endpoint_with_mock_data(client):
    """Test chat endpoint with TestModel (no API key required)."""
    # Note: TestModel provides invalid data to tool calls (e.g., 'a' for dates)
    # which causes tool execution to fail. This test is skipped for spike validation.
    # Real API testing would require OPENAI_API_KEY to be set.

    response = await client.post(
        "/chat", json={"message": "Hello", "user_id": "test-user"}
    )

    assert response.status_code == 200
    data = response.json()

    # TestModel returns minimal structured data
    assert "message" in data
    assert "data_sources_used" in data
    assert "confidence" in data
    assert isinstance(data["confidence"], (int, float))


async def test_visualization_generation(client):
    """Test visualization generation endpoint."""
    response = await client.post("/generate-viz")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "viz_id" in data
    assert "url" in data
    assert "generation_time_ms" in data

    # Verify generation time meets requirement (<3000ms)
    assert data["generation_time_ms"] < 3000, (
        f"Visualization took {data['generation_time_ms']}ms (>3000ms)"
    )

    # Verify we can fetch the generated image
    viz_id = data["viz_id"]
    viz_response = await client.get(f"/viz/{viz_id}")
    assert viz_response.status_code == 200
    assert viz_response.headers["content-type"] == "image/png"


async def test_visualization_not_found(client):
    """Test visualization endpoint with invalid ID."""
    response = await client.get("/viz/nonexistent-id")
    assert response.status_code == 404
