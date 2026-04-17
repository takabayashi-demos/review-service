"""Test suite for Review Service"""
import pytest
import json
from app import app, reviews_db, review_counter


@pytest.fixture
def client():
    """Configure test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database state before each test"""
    global reviews_db, review_counter
    reviews_db.clear()
    reviews_db.update({
        "P001": [
            {"id": "REV-001", "product_id": "P001", "user_id": "USR-001", "rating": 5, 
             "title": "Amazing TV!", "body": "Best 4K TV I've ever owned.", 
             "verified_purchase": True, "helpful_votes": 42, "created_at": "2024-11-15"},
        ],
    })


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_returns_up_status(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'UP'
        assert data['service'] == 'review-service'
        assert 'version' in data
    
    def test_ready_returns_ready_status(self, client):
        response = client.get('/ready')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'READY'


class TestGetReviews:
    """Test review retrieval endpoint"""
    
    def test_get_reviews_existing_product(self, client):
        response = client.get('/api/v1/reviews/P001')
        assert response.status_code == 200
        data = response.get_json()
        assert data['product_id'] == 'P001'
        assert data['total'] == 1
        assert data['average_rating'] == 5.0
        assert len(data['reviews']) == 1
        assert data['reviews'][0]['id'] == 'REV-001'
    
    def test_get_reviews_nonexistent_product(self, client):
        response = client.get('/api/v1/reviews/P999')
        assert response.status_code == 200
        data = response.get_json()
        assert data['product_id'] == 'P999'
        assert data['total'] == 0
        assert data['average_rating'] == 0
        assert data['reviews'] == []
    
    def test_get_reviews_calculates_average_correctly(self, client):
        reviews_db['P002'] = [
            {"id": "REV-002", "product_id": "P002", "user_id": "USR-001", "rating": 4, 
             "title": "Good", "body": "Nice product", "verified_purchase": True, 
             "helpful_votes": 10, "created_at": "2024-11-01"},
            {"id": "REV-003", "product_id": "P002", "user_id": "USR-002", "rating": 2, 
             "title": "Meh", "body": "Could be better", "verified_purchase": False, 
             "helpful_votes": 3, "created_at": "2024-11-02"},
        ]
        response = client.get('/api/v1/reviews/P002')
        data = response.get_json()
        assert data['average_rating'] == 3.0
        assert data['total'] == 2


class TestCreateReview:
    """Test review creation endpoint"""
    
    def test_create_review_valid_data(self, client):
        payload = {
            "product_id": "P003",
            "user_id": "USR-100",
            "rating": 4,
            "title": "Solid product",
            "body": "Works as expected, happy with purchase."
        }
        response = client.post('/api/v1/reviews', 
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert data['product_id'] == 'P003'
        assert data['rating'] == 4
        assert data['title'] == 'Solid product'
        assert 'id' in data
        assert data['verified_purchase'] is False
        assert data['helpful_votes'] == 0
    
    def test_create_review_adds_to_database(self, client):
        payload = {
            "product_id": "P001",
            "user_id": "USR-200",
            "rating": 3,
            "title": "Average",
            "body": "It's okay."
        }
        client.post('/api/v1/reviews',
                   data=json.dumps(payload),
                   content_type='application/json')
        
        response = client.get('/api/v1/reviews/P001')
        data = response.get_json()
        assert data['total'] == 2
    
    def test_create_review_missing_optional_fields(self, client):
        payload = {
            "product_id": "P004",
            "rating": 5
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(payload),
                              content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert data['title'] == ''
        assert data['body'] == ''
        assert data['user_id'] == 'anonymous'
    
    def test_create_review_empty_json(self, client):
        response = client.post('/api/v1/reviews',
                              data=json.dumps({}),
                              content_type='application/json')
        assert response.status_code == 201


class TestReviewStats:
    """Test review statistics endpoint"""
    
    def test_stats_single_product(self, client):
        response = client.get('/api/v1/reviews/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_reviews'] == 1
        assert data['products_reviewed'] == 1
        assert data['average_rating'] == 5.0
    
    def test_stats_multiple_products(self, client):
        reviews_db['P002'] = [
            {"id": "REV-002", "product_id": "P002", "user_id": "USR-002", "rating": 3,
             "title": "OK", "body": "Fine", "verified_purchase": True,
             "helpful_votes": 5, "created_at": "2024-10-01"},
        ]
        reviews_db['P003'] = [
            {"id": "REV-003", "product_id": "P003", "user_id": "USR-003", "rating": 4,
             "title": "Good", "body": "Nice", "verified_purchase": False,
             "helpful_votes": 2, "created_at": "2024-10-15"},
        ]
        
        response = client.get('/api/v1/reviews/stats')
        data = response.get_json()
        assert data['total_reviews'] == 3
        assert data['products_reviewed'] == 3
        assert data['average_rating'] == 4.0
    
    def test_stats_rating_distribution(self, client):
        reviews_db['P001'].append(
            {"id": "REV-004", "product_id": "P001", "user_id": "USR-004", "rating": 5,
             "title": "Great", "body": "Excellent", "verified_purchase": True,
             "helpful_votes": 20, "created_at": "2024-11-20"}
        )
        reviews_db['P002'] = [
            {"id": "REV-005", "product_id": "P002", "user_id": "USR-005", "rating": 1,
             "title": "Bad", "body": "Terrible", "verified_purchase": True,
             "helpful_votes": 8, "created_at": "2024-09-10"},
        ]
        
        response = client.get('/api/v1/reviews/stats')
        data = response.get_json()
        distribution = data['rating_distribution']
        assert distribution['1'] == 1
        assert distribution['5'] == 2
        assert distribution['2'] == 0
