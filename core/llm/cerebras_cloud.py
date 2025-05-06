"""Cerebras LLM wrapper."""

import cerebras.cloud.sdk
from . import LLM
from .. import models
from typing import Iterable

class Cerebras(LLM):
    def __init__(self, provider_config: models.config.ProviderConfig):
        self._client = cerebras.cloud.sdk.Cerebras(api_key=provider_config.api_key)
        super().__init__(provider_config.name)
    def _complete(self, messages: list) -> Iterable[str]:
        stream = self._client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            stream=True
        )
        try:
            for chunk in stream:
                yield chunk.choices[0].delta.content or ""
        finally:
            stream.close()
