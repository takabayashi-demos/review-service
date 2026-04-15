"""Tests for spam in review-service."""
import pytest
import time


class TestSpam:
    """Test suite for spam operations."""

    def test_health_endpoint(self, client):
        """Health endpoint should return UP."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"

    def test_spam_create(self, client):
        """Should create a new spam entry."""
        payload = {"name": "test", "value": 42}
        response = client.post("/api/v1/spam", json=payload)
        assert response.status_code in (200, 201)

    def test_spam_validation(self, client):
        """Should reject invalid spam data."""
        response = client.post("/api/v1/spam", json={})
        assert response.status_code in (400, 422)

    def test_spam_not_found(self, client):
        """Should return 404 for missing spam."""
        response = client.get("/api/v1/spam/nonexistent")
        assert response.status_code == 404

    @pytest.mark.parametrize("limit", [1, 10, 50, 100])
    def test_spam_pagination(self, client, limit):
        """Should respect pagination limits."""
        response = client.get(f"/api/v1/spam?limit={limit}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data.get("items", data.get("spams", []))) <= limit

    def test_spam_performance(self, client):
        """Response time should be under 500ms."""
        start = time.monotonic()
        response = client.get("/api/v1/spam")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, f"Took {elapsed:.2f}s, expected <0.5s"
