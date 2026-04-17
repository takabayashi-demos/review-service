"""Tests for review-service"""
import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_review_invalid_rating_too_high(client):
    """Test that ratings above 5 are rejected"""
    response = client.post('/api/v1/reviews', 
        data=json.dumps({
            'product_id': 'P999',
            'rating': 10,
            'title': 'Test',
            'body': 'Test body'
        }),
        content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'between 1 and 5' in data['error']

def test_create_review_invalid_rating_too_low(client):
    """Test that ratings below 1 are rejected"""
    response = client.post('/api/v1/reviews', 
        data=json.dumps({
            'product_id': 'P999',
            'rating': 0,
            'title': 'Test',
            'body': 'Test body'
        }),
        content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_create_review_missing_rating(client):
    """Test that missing rating is rejected"""
    response = client.post('/api/v1/reviews', 
        data=json.dumps({
            'product_id': 'P999',
            'title': 'Test',
            'body': 'Test body'
        }),
        content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'rating is required' in data['error']

def test_create_review_missing_product_id(client):
    """Test that missing product_id is rejected"""
    response = client.post('/api/v1/reviews', 
        data=json.dumps({
            'rating': 5,
            'title': 'Test',
            'body': 'Test body'
        }),
        content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'product_id is required' in data['error']

def test_create_review_valid(client):
    """Test that valid reviews are accepted"""
    response = client.post('/api/v1/reviews', 
        data=json.dumps({
            'product_id': 'P999',
            'rating': 5,
            'title': 'Great product',
            'body': 'Really happy with this purchase'
        }),
        content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['rating'] == 5
    assert data['product_id'] == 'P999'

def test_create_review_valid_rating_boundaries(client):
    """Test that boundary ratings (1 and 5) are accepted"""
    for rating in [1, 5]:
        response = client.post('/api/v1/reviews', 
            data=json.dumps({
                'product_id': 'P999',
                'rating': rating,
                'title': 'Test',
                'body': 'Test'
            }),
            content_type='application/json')
        assert response.status_code == 201
