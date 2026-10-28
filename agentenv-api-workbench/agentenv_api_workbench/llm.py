from __future__ import annotations

from typing import Protocol
from urllib.parse import urlsplit, urlunsplit


class ChatModel(Protocol):
    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, str | None]: ...


class OpenAIChatModel:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        azure_endpoint: str | None = None,
        api_version: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> None:
        self._api_mode = "chat_completions"
        if azure_endpoint and "/openai/v1" in azure_endpoint.casefold():
            from openai import OpenAI

            parts = urlsplit(azure_endpoint)
            path = parts.path.rstrip("/")
            if path.endswith("/responses"):
                path = path[: -len("/responses")]
            base_url = urlunsplit((parts.scheme, parts.netloc, path.rstrip("/") + "/", "", ""))
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self._api_mode = "responses"
        elif azure_endpoint:
            if not api_version:
                raise ValueError("api_version is required when using Azure OpenAI")
            from openai import AzureOpenAI

            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
            )
        else:
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, str | None]:
        if self._api_mode == "responses":
            response = self.client.responses.create(
                model=self.model,
                input=conversation,
                max_output_tokens=self.max_tokens,
            )
            return response.output_text or "", None

        response = self.client.chat.completions.create(
            model=self.model,
            messages=conversation,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        message = response.choices[0].message
        return message.content or "", getattr(message, "reasoning_content", None)