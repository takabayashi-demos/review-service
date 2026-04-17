"""Tests for review-service pagination"""
import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_reviews_without_pagination(client):
    """Test backward compatibility: no pagination params returns all reviews"""
    response = client.get("/api/v1/reviews/P001")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["product_id"] == "P001"
    assert len(data["reviews"]) == 2
    assert "pagination" not in data


def test_reviews_with_pagination(client):
    """Test pagination returns correct page of results"""
    response = client.get("/api/v1/reviews/P001?page=1&page_size=1")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert len(data["reviews"]) == 1
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 1
    assert data["pagination"]["total_pages"] == 2
    assert data["pagination"]["has_next"] is True
    assert data["pagination"]["has_prev"] is False


def test_pagination_second_page(client):
    """Test second page returns correct results"""
    response = client.get("/api/v1/reviews/P001?page=2&page_size=1")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert len(data["reviews"]) == 1
    assert data["pagination"]["page"] == 2
    assert data["pagination"]["has_next"] is False
    assert data["pagination"]["has_prev"] is True


def test_pagination_invalid_page(client):
    """Test invalid page number defaults to page 1"""
    response = client.get("/api/v1/reviews/P001?page=0&page_size=1")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["pagination"]["page"] == 1


def test_pagination_max_page_size(client):
    """Test page_size is capped at 100"""
    response = client.get("/api/v1/reviews/P001?page=1&page_size=500")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert data["pagination"]["page_size"] == 100


def test_pagination_empty_results(client):
    """Test pagination with product that has no reviews"""
    response = client.get("/api/v1/reviews/P999?page=1&page_size=10")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert len(data["reviews"]) == 0
    assert data["pagination"]["total_pages"] == 0
    assert data["pagination"]["has_next"] is False


def test_pagination_beyond_available(client):
    """Test requesting page beyond available reviews"""
    response = client.get("/api/v1/reviews/P001?page=10&page_size=10")
    data = json.loads(response.data)
    
    assert response.status_code == 200
    assert len(data["reviews"]) == 0
    assert data["pagination"]["has_next"] is False
