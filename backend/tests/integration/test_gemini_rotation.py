from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.providers import gemini
from app.providers.gemini import GoogleGeminiModelProvider

pytestmark = pytest.mark.integration


class TinyStructuredResponse(BaseModel):
    answer: str


class AuthFailure(Exception):
    status_code = 401


class ServiceFailure(Exception):
    status_code = 503


class RetryFailure(Exception):
    status_code = 429


class FakeGeminiModel:
    instances: list["FakeGeminiModel"] = []

    def __init__(self, *, api_key: str, **_kwargs: object) -> None:
        self.api_key = api_key
        self.calls = 0
        self.structured = False
        self.__class__.instances.append(self)

    def invoke(self, _messages: object) -> SimpleNamespace:
        self.calls += 1
        if self.api_key in {"retry-key-1", "retry-key-3"}:
            raise RetryFailure("rate limited")
        if self.structured:
            return {"answer": "structured"}  # type: ignore[return-value]
        return SimpleNamespace(content="ok")

    def with_structured_output(self, _schema: type[BaseModel]) -> "FakeGeminiModel":
        self.structured = True
        return self


def test_round_robin_and_retry_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeGeminiModel.instances = []
    monkeypatch.setattr(gemini, "ChatGoogleGenerativeAI", FakeGeminiModel)
    provider = GoogleGeminiModelProvider(
        model_name="gemini-3.5-flash-lite",
        api_keys=[
            ("GEMINI_API_KEY", "retry-key-1"),
            ("GEMINI_API_KEY_2", "working-key-2"),
            ("GEMINI_API_KEY_3", "retry-key-3"),
            ("GEMINI_API_KEY_4", "working-key-4"),
        ],
    )

    assert provider.generate_text("system", "first", task_name="first-task") == "ok"
    assert provider.generate_text("system", "second", task_name="second-task") == "ok"
    assert [instance.calls for instance in FakeGeminiModel.instances] == [1, 2, 0, 0]

    structured = provider.generate_structured(
        "system",
        "structured request",
        TinyStructuredResponse,
        task_name="structured-task",
    )
    assert structured.answer == "structured"


def test_non_retryable_error_does_not_rotate(monkeypatch: pytest.MonkeyPatch) -> None:
    class AuthFailureModel(FakeGeminiModel):
        def invoke(self, _messages: object) -> SimpleNamespace:
            self.calls += 1
            raise AuthFailure("invalid key")

    monkeypatch.setattr(gemini, "ChatGoogleGenerativeAI", AuthFailureModel)
    AuthFailureModel.instances = []
    provider = GoogleGeminiModelProvider(
        api_keys=[("GEMINI_API_KEY", "auth-key-1"), ("GEMINI_API_KEY_2", "auth-key-2")]
    )

    with pytest.raises(AuthFailure):
        provider.generate_text("system", "request", task_name="auth-task")
    assert [instance.calls for instance in AuthFailureModel.instances] == [1, 0]


def test_all_retryable_keys_raise_safe_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    class ServiceFailureModel(FakeGeminiModel):
        def invoke(self, _messages: object) -> SimpleNamespace:
            self.calls += 1
            raise ServiceFailure("service unavailable")

    monkeypatch.setattr(gemini, "ChatGoogleGenerativeAI", ServiceFailureModel)
    ServiceFailureModel.instances = []
    provider = GoogleGeminiModelProvider(
        api_keys=[("GEMINI_API_KEY", "secret-a"), ("GEMINI_API_KEY_2", "secret-b")]
    )

    with pytest.raises(Exception, match="all-keys-task.*2 configured key"):
        provider.generate_text("system", "request", task_name="all-keys-task")
    assert [instance.calls for instance in ServiceFailureModel.instances] == [1, 1]
