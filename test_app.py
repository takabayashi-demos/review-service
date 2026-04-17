"""Unit tests for Review Service"""
import pytest
import json
from app import app, reviews_db, helpful_votes_tracker

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def reset_votes():
    """Clear helpful votes tracker before each test"""
    helpful_votes_tracker.clear()
    yield

class TestHelpfulVotes:
    def test_mark_review_helpful_success(self, client):
        """Test successfully marking a review as helpful"""
        response = client.post(
            '/api/v1/reviews/REV-001/helpful',
            data=json.dumps({'user_id': 'USR-100'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['review_id'] == 'REV-001'
        assert data['helpful_votes'] == 43  # Was 42, now 43
        assert 'message' in data
    
    def test_mark_helpful_duplicate_vote(self, client):
        """Test that duplicate votes from same user are prevented"""
        # First vote succeeds
        response1 = client.post(
            '/api/v1/reviews/REV-001/helpful',
            data=json.dumps({'user_id': 'USR-100'}),
            content_type='application/json'
        )
        assert response1.status_code == 200
        
        # Second vote from same user fails
        response2 = client.post(
            '/api/v1/reviews/REV-001/helpful',
            data=json.dumps({'user_id': 'USR-100'}),
            content_type='application/json'
        )
        assert response2.status_code == 409
        data = json.loads(response2.data)
        assert 'already marked' in data['error'].lower()
    
    def test_mark_helpful_different_users(self, client):
        """Test that different users can vote on same review"""
        response1 = client.post(
            '/api/v1/reviews/REV-001/helpful',
            data=json.dumps({'user_id': 'USR-100'}),
            content_type='application/json'
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            '/api/v1/reviews/REV-001/helpful',
            data=json.dumps({'user_id': 'USR-200'}),
            content_type='application/json'
        )
        assert response2.status_code == 200
        data = json.loads(response2.data)
        assert data['helpful_votes'] == 44  # 42 + 2 votes
    
    def test_mark_helpful_missing_user_id(self, client):
        """Test that user_id is required"""
        response = client.post(
            '/api/v1/reviews/REV-001/helpful',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'user_id is required' in data['error']
    
    def test_mark_helpful_nonexistent_review(self, client):
        """Test voting on non-existent review returns 404"""
        response = client.post(
            '/api/v1/reviews/REV-999/helpful',
            data=json.dumps({'user_id': 'USR-100'}),
            content_type='application/json'
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()

class TestExistingEndpoints:
    def test_health_check(self, client):
        """Ensure health endpoint still works"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'UP'
    
    def test_get_reviews(self, client):
        """Ensure get reviews endpoint still works"""
        response = client.get('/api/v1/reviews/P001')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['product_id'] == 'P001'
        assert len(data['reviews']) == 2
