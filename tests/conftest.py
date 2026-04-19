"""Shared pytest fixtures for the motivational quote app test suite."""
from unittest.mock import MagicMock, patch

import pytest

from app import app as flask_app


@pytest.fixture
def client():
    """Flask test client with testing mode enabled."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def mock_anthropic():
    """
    Patch app.client so no real Anthropic API calls are made.

    Usage:
        def test_something(client, mock_anthropic):
            mock_anthropic.return_value = "Stay focused."
            response = client.post("/", data={"work": "coding"})
            ...

    Setting mock_anthropic.return_value changes the text returned by
    client.messages.create().content[0].text in the app.
    """
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Keep going, you're doing great.")]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    # Helper to change the returned quote text
    def set_return_value(text: str) -> None:
        mock_message.content[0].text = text

    mock_client.return_value = set_return_value

    with patch("app.client", mock_client):
        yield mock_client


@pytest.fixture
def mock_anthropic_error():
    """Patch app.client to raise an exception — simulates API failure."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("Anthropic API unavailable")

    with patch("app.client", mock_client):
        yield mock_client
