"""Tests for the /ping endpoint."""


def test_ping_status_code(client):
    """GET /ping returns HTTP 200."""
    response = client.get("/ping")
    assert response.status_code == 200


def test_ping_content_type(client):
    """GET /ping returns application/json content type."""
    response = client.get("/ping")
    assert response.mimetype == "application/json"


def test_ping_json_body(client):
    """GET /ping response contains {"pong": true}."""
    response = client.get("/ping")
    data = response.get_json()
    assert data == {"pong": True}
