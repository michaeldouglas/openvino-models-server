import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from conftest import FakeProvider
from local_llm.config import Settings
from local_llm.main import create_app


def test_settings_reject_undeclared_remote_provider() -> None:
    with pytest.raises(ValidationError):
        Settings(provider="openai")


def test_local_runtime_does_not_accept_remote_url_as_model_selector() -> None:
    provider = FakeProvider()
    with TestClient(create_app(Settings(), provider)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "https://api.openai.com/v1",
                "messages": [{"role": "user", "content": "Oi"}],
            },
        )

    assert response.status_code == 404
    assert provider.async_calls == 0
