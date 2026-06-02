import pytest
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['API_KEY'] = 'test_key'

from app import app
from database import db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['CACHE_TYPE'] = 'simple'
    app.config['CACHE_NO_NULL_WARNING'] = True

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_league_not_found(client):
    response = client.get('/league/nonexistent-league')
    assert response.status_code == 404

def test_top_scorer_route(client):
    response = client.get('/top-scorer')
    assert response.status_code == 200

def test_top_assists_route(client):
    response = client.get('/top-assists')
    assert response.status_code == 200

def test_player_comparison_route(client):
    response = client.get('/player_comparison')
    assert response.status_code == 200

def test_player_tracker_route(client):
    response = client.get('/player-tracker')
    assert response.status_code == 200

def test_404_handler(client):
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
