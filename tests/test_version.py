"""Tests for the /version endpoint."""
import platform
from datetime import date


def test_version_status_code(client):
    """GET /version returns HTTP 200."""
    response = client.get("/version")
    assert response.status_code == 200


def test_version_content_type(client):
    """GET /version returns application/json content type."""
    response = client.get("/version")
    assert response.mimetype == "application/json"


def test_version_json_has_python_version(client):
    """GET /version response contains python_version matching platform.python_version()."""
    response = client.get("/version")
    data = response.get_json()
    assert "python_version" in data
    assert data["python_version"] == platform.python_version()


def test_version_json_has_date(client):
    """GET /version response contains date in ISO format matching today's date."""
    today_before = date.today().isoformat()
    response = client.get("/version")
    today_after = date.today().isoformat()
    data = response.get_json()
    assert "date" in data
    assert data["date"] in (today_before, today_after)
