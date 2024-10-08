
# test_core.py
import pytest
from main import app
from flask_jwt_extended import create_access_token
from typing import Generator, Dict
from flask.testing import FlaskClient

@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

def get_auth_header() -> Dict[str, str]:
    access_token = create_access_token(identity="testuser")
    return {"Authorization": f"Bearer {access_token}"}

class TestRouterApp:
    def test_all_strategy(self, client: FlaskClient) -> None:
        response = client.post('/api/events', json={
            "payload": {"a": 1},
            "routingIntents": [
                {"destinationName": "destination1", "important": True, "bytes": 500},
                {"destinationName": "destination2", "important": True, "bytes": 1500},
                {"destinationName": "destination3", "important": False, "bytes": 200},
                {"destinationName": "destination4", "important": False, "bytes": 3000},
                {"destinationName": "destination5", "important": True, "bytes": 1000}
            ],
            "strategy": "ALL"
        }, headers=get_auth_header())
        assert response.status_code == 200
        assert response.json == {
            "destination1": True,
            "destination2": True,
            "destination3": True,
            "destination4": True,
            "destination5": True
        }

    def test_important_strategy(self, client: FlaskClient) -> None:
        response = client.post('/api/events', json={
            "payload": {"a": 1},
            "routingIntents": [
                {"destinationName": "destination1", "important": True, "bytes": 500},
                {"destinationName": "destination2", "important": False, "bytes": 1500},
                {"destinationName": "destination3", "important": True, "bytes": 200},
                {"destinationName": "destination4", "important": False, "bytes": 3000},
                {"destinationName": "destination5", "important": True, "bytes": 1000}
            ],
            "strategy": "IMPORTANT"
        }, headers=get_auth_header())
        assert response.status_code == 200
        assert response.json == {
            "destination1": True,
            "destination2": False,
            "destination3": True,
            "destination4": False,
            "destination5": True
        }

    def test_small_strategy(self, client: FlaskClient) -> None:
        response = client.post('/api/events', json={
            "payload": {"a": 1},
            "routingIntents": [
                {"destinationName": "destination1", "important": True, "bytes": 512},
                {"destinationName": "destination2", "important": False, "bytes": 2048},
                {"destinationName": "destination3", "important": True, "bytes": 1024},
                {"destinationName": "destination4", "important": False, "bytes": 256}
            ],
            "strategy": "SMALL"
        }, headers=get_auth_header())
        assert response.status_code == 200
        assert response.json == {
            "destination1": True,
            "destination2": False,
            "destination3": False,
            "destination4": True
        }

    def test_custom_strategy(self, client: FlaskClient) -> None:
        response = client.post('/api/events', json={
            "payload": {"a": 1},
            "strategy": "lambda routing_intents: [intent for intent in routing_intents if intent.get('score', 0) < 0]",
            "routingIntents": [
                {"destinationName": "destination1", "important": True, "bytes": 500, "score": 1},
                {"destinationName": "destination2", "important": False, "bytes": 1500, "score": -1},
                {"destinationName": "destination3", "important": True, "bytes": 200, "score": 0},
                {"destinationName": "destination4", "important": False, "bytes": 3000, "score": -1},
                {"destinationName": "destination5", "important": True, "bytes": 1000, "score": 1}
            ]
        }, headers=get_auth_header())
        assert response.status_code == 200
        assert response.json == {
            "destination1": False,
            "destination2": True,
            "destination3": False,
            "destination4": True,
            "destination5": False
        }

    def test_invalid_payload(self, client: FlaskClient) -> None:
        response = client.post('/api/events', json={
            "invalid": "data"
        }, headers=get_auth_header())
        assert response.status_code == 400
        assert "error" in response.json