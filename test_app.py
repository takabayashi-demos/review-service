"""Unit tests for Review Service

Tests cover happy paths, edge cases, and document known vulnerabilities.
"""
import pytest
import json
from app import app


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_reviews_db():
    """Reset database to initial state before each test"""
    from app import reviews_db
    reviews_db.clear()
    reviews_db.update({
        "P001": [
            {"id": "REV-001", "product_id": "P001", "user_id": "USR-001", "rating": 5,
             "title": "Amazing TV!", "body": "Best 4K TV I've ever owned.",
             "verified_purchase": True, "helpful_votes": 42, "created_at": "2024-11-15"},
        ]
    })


class TestHealthEndpoints:
    """Test health and readiness endpoints"""

    def test_health_check(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'UP'
        assert data['service'] == 'review-service'
        assert 'version' in data

    def test_ready_check(self, client):
        response = client.get('/ready')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'READY'


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

    def test_get_reviews_nonexistent_product(self, client):
        response = client.get('/api/v1/reviews/P999')
        assert response.status_code == 200
        data = response.get_json()
        assert data['product_id'] == 'P999'
        assert data['reviews'] == []
        assert data['total'] == 0
        assert data['average_rating'] == 0

    def test_average_rating_multiple_reviews(self, client):
        from app import reviews_db
        reviews_db['P002'] = [
            {"id": "REV-010", "product_id": "P002", "user_id": "U1", "rating": 2,
             "title": "Meh", "body": "Could be better", "verified_purchase": True,
             "helpful_votes": 1, "created_at": "2024-01-01"},
            {"id": "REV-011", "product_id": "P002", "user_id": "U2", "rating": 4,
             "title": "Good", "body": "Pretty good", "verified_purchase": True,
             "helpful_votes": 5, "created_at": "2024-01-02"},
        ]
        response = client.get('/api/v1/reviews/P002')
        data = response.get_json()
        assert data['average_rating'] == 3.0
        assert data['total'] == 2


class TestCreateReview:
    """Test review creation endpoint"""

    def test_create_review_happy_path(self, client):
        review_data = {
            "product_id": "P001",
            "user_id": "USR-002",
            "rating": 4,
            "title": "Good product",
            "body": "Works as expected, very satisfied"
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert data['rating'] == 4
        assert data['title'] == "Good product"
        assert data['product_id'] == "P001"
        assert 'id' in data
        assert data['verified_purchase'] is False
        assert data['helpful_votes'] == 0

    def test_create_review_minimal_fields(self, client):
        review_data = {
            "product_id": "P002",
            "rating": 3
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert data['rating'] == 3
        assert data['product_id'] == 'P002'
        assert data['title'] == ""
        assert data['body'] == ""

    def test_create_review_new_product(self, client):
        """Test creating first review for new product"""
        review_data = {
            "product_id": "P999",
            "rating": 5,
            "title": "First review",
            "body": "Great product"
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        assert response.status_code == 201

        # Verify it appears in product reviews
        get_response = client.get('/api/v1/reviews/P999')
        assert get_response.get_json()['total'] == 1


class TestKnownBugs:
    """Tests documenting known security and validation bugs"""

    def test_xss_vulnerability_in_review_body(self, client):
        """Documents XSS vulnerability - user input not sanitized"""
        xss_payload = "<script>alert('xss')</script>"
        review_data = {
            "product_id": "P003",
            "rating": 5,
            "title": "Test",
            "body": xss_payload
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        # BUG: XSS payload stored unsanitized
        assert xss_payload in data['body']

    def test_xss_vulnerability_in_title(self, client):
        """Documents XSS vulnerability in title field"""
        xss_payload = "<img src=x onerror=alert(1)>"
        review_data = {
            "product_id": "P004",
            "rating": 4,
            "title": xss_payload
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        assert response.status_code == 201
        # BUG: XSS payload stored unsanitized
        assert response.get_json()['title'] == xss_payload

    def test_rating_out_of_range_high(self, client):
        """Documents missing validation - accepts rating > 5"""
        review_data = {
            "product_id": "P005",
            "rating": 999,
            "title": "Invalid rating"
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        # BUG: Should reject, but currently accepts
        assert response.status_code == 201
        assert response.get_json()['rating'] == 999

    def test_rating_negative(self, client):
        """Documents missing validation - accepts negative ratings"""
        review_data = {
            "product_id": "P006",
            "rating": -5
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        # BUG: Should reject, but currently accepts
        assert response.status_code == 201
        assert response.get_json()['rating'] == -5

    def test_extremely_long_title(self, client):
        """Documents missing length validation on title"""
        long_title = "A" * 50000  # 50KB title
        review_data = {
            "product_id": "P007",
            "rating": 5,
            "title": long_title
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        # BUG: Should reject or truncate, but currently accepts
        assert response.status_code == 201
        assert len(response.get_json()['title']) == 50000

    def test_extremely_long_body(self, client):
        """Documents missing length validation on body"""
        long_body = "B" * 100000  # 100KB body
        review_data = {
            "product_id": "P008",
            "rating": 3,
            "body": long_body
        }
        response = client.post('/api/v1/reviews',
                              data=json.dumps(review_data),
                              content_type='application/json')
        # BUG: Should reject or truncate, but currently accepts
        assert response.status_code == 201
        assert len(response.get_json()['body']) == 100000


class TestReviewStats:
    """Test review statistics endpoint"""

    def test_stats_with_single_product(self, client):
        response = client.get('/api/v1/reviews/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_reviews'] == 1
        assert data['products_reviewed'] == 1
        assert data['average_rating'] == 5.0
        assert '5' in data['rating_distribution']

    def test_stats_empty_database(self, client):
        from app import reviews_db
        reviews_db.clear()
        response = client.get('/api/v1/reviews/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_reviews'] == 0
        assert data['products_reviewed'] == 0
        assert data['average_rating'] == 0

    def test_rating_distribution(self, client):
        # Add reviews with various ratings
        for rating in [1, 2, 3, 4, 5, 5, 5]:
            client.post('/api/v1/reviews',
                       data=json.dumps({"product_id": "P010", "rating": rating}),
                       content_type='application/json')

        response = client.get('/api/v1/reviews/stats')
        data = response.get_json()
        distribution = data['rating_distribution']
        assert distribution['1'] == 1
        assert distribution['2'] == 1
        assert distribution['3'] == 1
        assert distribution['4'] == 1
        assert distribution['5'] == 4  # 1 from fixture + 3 new

    def test_stats_multiple_products(self, client):
        client.post('/api/v1/reviews',
                   data=json.dumps({"product_id": "P020", "rating": 4}),
                   content_type='application/json')
        client.post('/api/v1/reviews',
                   data=json.dumps({"product_id": "P021", "rating": 3}),
                   content_type='application/json')

        response = client.get('/api/v1/reviews/stats')
        data = response.get_json()
        assert data['products_reviewed'] == 3  # P001 + P020 + P021
        assert data['total_reviews'] == 3
