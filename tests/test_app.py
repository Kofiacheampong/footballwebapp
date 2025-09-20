import pytest
import os
# Set test environment before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['API_KEY'] = 'test_key'

from app import app
from database import db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

def test_health_check(client):
    """Test basic health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_detailed_health_check(client):
    """Test detailed health check endpoint"""
    response = client.get('/health/detailed')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'checks' in data

def test_index_route(client):
    """Test index route"""
    response = client.get('/')
    assert response.status_code == 200

def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'football_app_cpu_usage' in response.get_data(as_text=True)