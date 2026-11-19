from collections.abc import Callable, Sequence
from threading import Lock

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ValidationError

from app.core.errors import ExternalProviderError, RetryableExternalProviderError
from app.providers.base import ResponseModel


class GoogleGeminiModelProvider:
    """Gemini adapter with bounded key rotation and no provider retries."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-3.5-flash-lite",
        *,
        api_keys: Sequence[tuple[str, str]] | None = None,
    ) -> None:
        configured_keys = list(api_keys or [])
        if not configured_keys and api_key:
            configured_keys = [("GEMINI_API_KEY", api_key)]
        if not configured_keys:
            raise ExternalProviderError("Gemini has no configured API keys")
        self._model_name = model_name
        self._models = [
            (
                label,
                ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=key,
                    temperature=0.1,
                    max_retries=0,
                ),
            )
            for label, key in configured_keys
        ]
        self._rotation_lock = Lock()
        self._next_start_index = 0

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        task_name: str = "generate_text",
    ) -> str:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

        def invoke(model: ChatGoogleGenerativeAI) -> str:
            response = model.invoke(messages)
            if isinstance(response.content, str):
                return response.content
            return "\n".join(str(block) for block in response.content)

        result = self._invoke_with_rotation(task_name, invoke)
        return str(result)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[ResponseModel],
        *,
        task_name: str | None = None,
    ) -> ResponseModel:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        operation_name = task_name or f"structured:{schema.__name__}"

        def invoke(model: ChatGoogleGenerativeAI) -> ResponseModel:
            structured_model = model.with_structured_output(schema)
            response = structured_model.invoke(messages)
            if isinstance(response, BaseModel):
                return schema.model_validate(response)
            return schema.model_validate(response)

        result = self._invoke_with_rotation(operation_name, invoke)
        return schema.model_validate(result)

    def _invoke_with_rotation(
        self,
        task_name: str,
        invoke: Callable[[ChatGoogleGenerativeAI], ResponseModel | str],
    ) -> ResponseModel | str:
        with self._rotation_lock:
            start_index = self._next_start_index
            self._next_start_index = (self._next_start_index + 1) % len(self._models)

        attempted = 0
        for offset in range(len(self._models)):
            _label, model = self._models[(start_index + offset) % len(self._models)]
            attempted += 1
            try:
                return invoke(model)
            except (ValidationError, OutputParserException):
                raise
            except Exception as error:
                if not _is_retryable_provider_error(error):
                    raise

        raise RetryableExternalProviderError(
            f"Gemini task '{task_name}' failed after trying {attempted} configured key(s)"
        )


def _is_retryable_provider_error(error: BaseException) -> bool:
    return _extract_status_code(error) in {429, 503, 504}


def _extract_status_code(error: BaseException) -> int | None:
    candidates: list[object] = [
        getattr(error, "status_code", None),
        getattr(error, "status", None),
        getattr(error, "code", None),
    ]
    response = getattr(error, "response", None)
    if response is not None:
        candidates.append(getattr(response, "status_code", None))
    for candidate in candidates:
        if isinstance(candidate, int):
            return candidate
        if isinstance(candidate, str) and candidate.isdigit():
            return int(candidate)
    return None
