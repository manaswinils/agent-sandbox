from app import app


def test_health_endpoint_returns_200():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_json_content_type():
    client = app.test_client()
    response = client.get("/health")
    assert response.content_type == "application/json"


def test_health_endpoint_returns_status_ok():
    client = app.test_client()
    response = client.get("/health")
    assert response.get_json() == {"status": "ok"}
