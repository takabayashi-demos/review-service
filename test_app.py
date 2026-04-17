"""Tests for review service security fixes"""
import pytest
import json
from app import app, reviews_db, review_counter

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_xss_prevention_in_title(client):
    """Test that script tags in title are escaped"""
    malicious_review = {
        "product_id": "P999",
        "rating": 5,
        "title": "<script>alert('xss')</script>",
        "body": "Normal body text"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(malicious_review),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    # Script tags should be escaped
    assert "<script>" not in data["title"]
    assert "&lt;script&gt;" in data["title"]

def test_xss_prevention_in_body(client):
    """Test that script tags in body are escaped"""
    malicious_review = {
        "product_id": "P999",
        "rating": 5,
        "title": "Good product",
        "body": "Great! <img src=x onerror=alert('xss')>"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(malicious_review),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert "<img" not in data["body"]
    assert "&lt;img" in data["body"]

def test_rating_validation_too_high(client):
    """Test that rating above 5 is rejected"""
    invalid_review = {
        "product_id": "P999",
        "rating": 999,
        "title": "Test",
        "body": "Test body"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(invalid_review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "rating must be an integer between 1 and 5" in data["details"]

def test_rating_validation_too_low(client):
    """Test that rating below 1 is rejected"""
    invalid_review = {
        "product_id": "P999",
        "rating": -5,
        "title": "Test",
        "body": "Test body"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(invalid_review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "rating must be an integer between 1 and 5" in data["details"]

def test_title_length_limit(client):
    """Test that titles exceeding 200 chars are rejected"""
    invalid_review = {
        "product_id": "P999",
        "rating": 5,
        "title": "A" * 201,
        "body": "Test body"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(invalid_review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "title must not exceed 200 characters" in data["details"]

def test_body_length_limit(client):
    """Test that body exceeding 5000 chars is rejected"""
    invalid_review = {
        "product_id": "P999",
        "rating": 5,
        "title": "Test",
        "body": "A" * 5001
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(invalid_review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "body must not exceed 5000 characters" in data["details"]

def test_valid_review_still_works(client):
    """Test that valid reviews are accepted"""
    valid_review = {
        "product_id": "P999",
        "rating": 5,
        "title": "Great product!",
        "body": "I really enjoyed this product. Highly recommend."
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(valid_review),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["rating"] == 5
    assert data["title"] == "Great product!"
    assert data["body"] == "I really enjoyed this product. Highly recommend."
