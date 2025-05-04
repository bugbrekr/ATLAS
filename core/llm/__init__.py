"""Low-level LLM API utilities."""

from dataclasses import dataclass
from typing import Iterable

from .. import models

@dataclass
class LLM:
    provider_name: str
    model_name: str = None
    def __init__(self, provider_name:str):
        self.provider_name = provider_name # this is different from the provider name in the config
    def set_model_name(self, model_name: str):
        self.model_name = model_name
    def _complete(self, messages: list):
        raise NotImplementedError("Subclasses should implement this method.")
    def complete(self, history: models.chat.History, system_prompt: str = None) -> Iterable[str]:
        messages = history.to_messages()
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        for chunk in self._complete(messages):
            yield chunk

from . import (
    cerebras_cloud
)

def factory(provider_config: models.config.ProviderConfig) -> LLM:
    match provider_config.provider_name:
        case "cerebras":
            return cerebras_cloud.Cerebras(provider_config)
        case _:
            raise ValueError(f"Unknown provider: {provider_config.provider_name}")
