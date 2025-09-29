import json
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _auth_headers():
    return {"x-api-key": "test-key"}


def test_auth_error_missing_key():
    r = client.post("/ai/respond", json={"prompt": "hi"})
    assert r.status_code == 401


@pytest.mark.skip(reason="Requires mocking OpenAI responses.stream; implement with monkeypatch/mocks")
def test_respond_stream_happy(monkeypatch):
    # Example structure; actual implementation would mock openai client and stream events
    pass


