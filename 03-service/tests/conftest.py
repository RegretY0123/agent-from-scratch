from types import SimpleNamespace

import pytest
from app import app
from deps import get_llm_client
from fastapi.testclient import TestClient


class FakeClient:
    def __init__(self, answer="假回答", tokens=42, tool_calls=None):
        self.answer = answer
        self.tokens = tokens
        self.tool_calls = tool_calls
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(
                        content=self.answer, tool_calls=self.tool_calls
                    ),
                )
            ],
            usage=SimpleNamespace(total_tokens=self.tokens),
        )


@pytest.fixture
def fake_client():
    return FakeClient()


@pytest.fixture
def client(fake_client):
    app.dependency_overrides[get_llm_client] = lambda: fake_client
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
