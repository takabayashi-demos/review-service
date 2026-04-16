"""Tests for Review Service API endpoints."""
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "UP"
    assert data["service"] == "review-service"


def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "READY"


def test_get_reviews_existing_product(client):
    resp = client.get("/api/v1/reviews/P001")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["product_id"] == "P001"
    assert data["total"] == 2
    assert 1 <= data["average_rating"] <= 5
    assert len(data["reviews"]) == 2


def test_get_reviews_missing_product(client):
    resp = client.get("/api/v1/reviews/NONEXISTENT")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["reviews"] == []
    assert data["average_rating"] == 0


def test_create_review(client):
    payload = {
        "product_id": "P099",
        "rating": 4,
        "title": "Good product",
        "body": "Works as expected.",
        "user_id": "USR-TEST",
    }
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["product_id"] == "P099"
    assert data["rating"] == 4
    assert data["user_id"] == "USR-TEST"
    assert data["verified_purchase"] is False
    assert data["helpful_votes"] == 0


def test_create_review_defaults(client):
    payload = {"product_id": "P100", "rating": 3}
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["user_id"] == "anonymous"
    assert data["title"] == ""
    assert data["body"] == ""


def test_review_stats(client):
    resp = client.get("/api/v1/reviews/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_reviews" in data
    assert "products_reviewed" in data
    assert "average_rating" in data
    assert "rating_distribution" in data
    for key in ["1", "2", "3", "4", "5"]:
        assert key in data["rating_distribution"]


def test_created_review_appears_in_get(client):
    payload = {
        "product_id": "P200",
        "rating": 5,
        "title": "Love it",
        "body": "Highly recommend.",
    }
    client.post("/api/v1/reviews", json=payload)
    resp = client.get("/api/v1/reviews/P200")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["reviews"][0]["title"] == "Love it"
    assert data["average_rating"] == 5.0
