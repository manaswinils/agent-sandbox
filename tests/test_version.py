"""Tests for the /version endpoint."""
import sys
from datetime import date


def test_version_status_code(client):
    """GET /version returns HTTP 200."""
    response = client.get("/version")
    assert response.status_code == 200


def test_version_content_type(client):
    """GET /version returns application/json content type."""
    response = client.get("/version")
    assert response.content_type == "application/json"


def test_version_json_has_python_version(client):
    """GET /version response contains python_version matching sys.version."""
    response = client.get("/version")
    data = response.get_json()
    assert "python_version" in data
    assert data["python_version"] == sys.version


def test_version_json_has_date(client):
    """GET /version response contains date in ISO format matching today's date."""
    response = client.get("/version")
    data = response.get_json()
    assert "date" in data
    assert data["date"] == date.today().isoformat()
