from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.providers.base import ResponseModel


class GoogleGeminiModelProvider:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._model_name = model_name
        self._model = ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=0.1)

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self._model.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        if isinstance(response.content, str):
            return response.content
        return "\n".join(str(block) for block in response.content)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[ResponseModel],
    ) -> ResponseModel:
        structured_model = self._model.with_structured_output(schema)
        response = structured_model.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        if isinstance(response, BaseModel):
            return cast(ResponseModel, response)
        return schema.model_validate(response)
