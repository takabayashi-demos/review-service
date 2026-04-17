"""Tests for Review Service"""
import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'UP'
    assert data['service'] == 'review-service'

def test_mark_review_helpful(client):
    """Test marking a review as helpful"""
    response = client.post('/api/v1/reviews/REV-001/helpful')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['review_id'] == 'REV-001'
    assert 'helpful_votes' in data
    assert data['message'] == 'Review marked as helpful'

def test_mark_review_helpful_increments_count(client):
    """Test that helpful votes increment correctly"""
    # Get initial count
    response = client.get('/api/v1/reviews/P001')
    data = json.loads(response.data)
    initial_votes = data['reviews'][0]['helpful_votes']
    
    # Mark as helpful
    client.post('/api/v1/reviews/REV-001/helpful')
    
    # Verify count increased
    response = client.get('/api/v1/reviews/P001')
    data = json.loads(response.data)
    new_votes = data['reviews'][0]['helpful_votes']
    assert new_votes == initial_votes + 1

def test_mark_nonexistent_review_helpful(client):
    """Test marking a non-existent review as helpful"""
    response = client.post('/api/v1/reviews/REV-999/helpful')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Review not found'

def test_get_reviews(client):
    """Test getting reviews for a product"""
    response = client.get('/api/v1/reviews/P001')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['product_id'] == 'P001'
    assert len(data['reviews']) > 0

def test_create_review(client):
    """Test creating a new review"""
    new_review = {
        "product_id": "P999",
        "user_id": "USR-TEST",
        "rating": 5,
        "title": "Test Review",
        "body": "This is a test review"
    }
    response = client.post('/api/v1/reviews', 
                          data=json.dumps(new_review),
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['product_id'] == 'P999'
    assert data['rating'] == 5

def test_review_stats(client):
    """Test review statistics endpoint"""
    response = client.get('/api/v1/reviews/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_reviews' in data
    assert 'products_reviewed' in data
    assert 'average_rating' in data
