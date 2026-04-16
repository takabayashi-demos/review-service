import pytest
import json
from app import app, reviews_db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_db():
    """Snapshot and restore reviews_db between tests."""
    import copy
    original = copy.deepcopy(reviews_db)
    yield
    reviews_db.clear()
    reviews_db.update(original)


# -- Health / Ready ----------------------------------------------------------

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "UP"
    assert data["service"] == "review-service"
    assert "version" in data


def test_ready(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "READY"


# -- GET /api/v1/reviews/<product_id> ----------------------------------------

def test_get_reviews_existing_product(client):
    resp = client.get("/api/v1/reviews/P001")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["product_id"] == "P001"
    assert data["total"] == 2
    assert data["average_rating"] == 4.5
    assert len(data["reviews"]) == 2


def test_get_reviews_nonexistent_product(client):
    resp = client.get("/api/v1/reviews/NOPE")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["reviews"] == []
    assert data["average_rating"] == 0


def test_get_reviews_single_review_product(client):
    resp = client.get("/api/v1/reviews/P002")
    data = resp.get_json()
    assert data["total"] == 1
    assert data["average_rating"] == 5.0


# -- POST /api/v1/reviews ----------------------------------------------------

def test_create_review_happy_path(client):
    payload = {
        "product_id": "P001",
        "user_id": "USR-099",
        "rating": 4,
        "title": "Solid purchase",
        "body": "Works well for the price.",
    }
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["product_id"] == "P001"
    assert data["rating"] == 4
    assert data["verified_purchase"] is False
    assert data["helpful_votes"] == 0
    assert data["id"].startswith("REV-")

    # Verify it shows up on a subsequent GET
    get_resp = client.get("/api/v1/reviews/P001")
    assert get_resp.get_json()["total"] == 3


def test_create_review_new_product(client):
    payload = {
        "product_id": "P999",
        "rating": 3,
        "title": "Meh",
        "body": "It was okay.",
    }
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201

    get_resp = client.get("/api/v1/reviews/P999")
    assert get_resp.get_json()["total"] == 1


def test_create_review_defaults_to_anonymous(client):
    payload = {"product_id": "P001", "rating": 5}
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["user_id"] == "anonymous"


def test_create_review_missing_body_and_title(client):
    payload = {"product_id": "P001", "rating": 3}
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == ""
    assert data["body"] == ""


def test_create_review_out_of_range_rating_accepted(client):
    """Documents known bug: no rating bounds validation."""
    payload = {"product_id": "P001", "rating": 999}
    resp = client.post("/api/v1/reviews", json=payload)
    # Currently accepted -- this test documents the gap
    assert resp.status_code == 201
    assert resp.get_json()["rating"] == 999


def test_create_review_negative_rating_accepted(client):
    """Documents known bug: negative ratings accepted."""
    payload = {"product_id": "P001", "rating": -5}
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["rating"] == -5


def test_create_review_xss_in_body_stored_raw(client):
    """Documents known vulnerability: XSS payload stored unsanitized."""
    xss_body = '<script>alert("xss")</script>'
    payload = {"product_id": "P001", "rating": 1, "body": xss_body}
    resp = client.post("/api/v1/reviews", json=payload)
    assert resp.status_code == 201
    # Body is stored and returned without sanitization
    assert resp.get_json()["body"] == xss_body


# -- GET /api/v1/reviews/stats -----------------------------------------------

def test_stats_initial_data(client):
    resp = client.get("/api/v1/reviews/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_reviews"] == 4
    assert data["products_reviewed"] == 3
    assert data["average_rating"] == 4.8  # (5+4+5+5)/4
    assert "rating_distribution" in data
    assert data["rating_distribution"]["5"] == 3
    assert data["rating_distribution"]["4"] == 1


def test_stats_updates_after_new_review(client):
    payload = {"product_id": "P001", "rating": 1, "title": "Bad", "body": "Broken."}
    client.post("/api/v1/reviews", json=payload)

    resp = client.get("/api/v1/reviews/stats")
    data = resp.get_json()
    assert data["total_reviews"] == 5
    assert data["rating_distribution"]["1"] == 1
