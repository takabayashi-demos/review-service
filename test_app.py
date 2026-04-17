"""Tests for review-service security fixes"""
import pytest
import json
from app import app, reviews_db, review_counter

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_xss_sanitization(client):
    """Test that HTML/JS in review is escaped"""
    malicious_review = {
        "product_id": "P999",
        "user_id": "USR-999",
        "rating": 5,
        "title": "<script>alert('xss')</script>Great product",
        "body": "Love it! <img src=x onerror=alert('xss')>"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(malicious_review),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    
    # Verify HTML is escaped
    assert '&lt;script&gt;' in data['title']
    assert '&lt;img' in data['body']
    assert '<script>' not in data['title']
    assert 'onerror=' not in data['body']

def test_rating_validation_too_high(client):
    """Test that ratings above 5 are rejected"""
    review = {
        "product_id": "P001",
        "rating": 999,
        "title": "Test",
        "body": "Test"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'rating must be between' in data['error']

def test_rating_validation_too_low(client):
    """Test that ratings below 1 are rejected"""
    review = {
        "product_id": "P001",
        "rating": -5,
        "title": "Test",
        "body": "Test"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'rating must be between' in data['error']

def test_rating_validation_invalid_type(client):
    """Test that non-integer ratings are rejected"""
    review = {
        "product_id": "P001",
        "rating": "not a number",
        "title": "Test",
        "body": "Test"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'must be a valid integer' in data['error']

def test_title_length_validation(client):
    """Test that overly long titles are rejected"""
    review = {
        "product_id": "P001",
        "rating": 5,
        "title": "A" * 201,  # Exceeds MAX_TITLE_LENGTH
        "body": "Test"
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'title must be' in data['error']

def test_body_length_validation(client):
    """Test that overly long bodies are rejected"""
    review = {
        "product_id": "P001",
        "rating": 5,
        "title": "Test",
        "body": "B" * 5001  # Exceeds MAX_BODY_LENGTH
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(review),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'body must be' in data['error']

def test_valid_review_accepted(client):
    """Test that valid reviews are still accepted"""
    review = {
        "product_id": "P001",
        "user_id": "USR-100",
        "rating": 4,
        "title": "Good product",
        "body": "I really enjoyed this product. Would recommend."
    }
    
    response = client.post('/api/v1/reviews',
                          data=json.dumps(review),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['rating'] == 4
    assert data['title'] == "Good product"
