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
    def _complete(self, messages: list) -> Iterable[str]:
        raise NotImplementedError("Subclasses should implement this method.")
    def complete(self, history: models.chat.History, system_prompt: str = None) -> Iterable[str]:
        messages = history.to_messages()
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        for chunk in self._complete(messages):
            for i in chunk:
                yield i

# Import all LLM providers
from . import (
    cerebras_cloud
)

PROVIDERS = {
    "cerebras": cerebras_cloud.Cerebras
}

def factory(provider_config: models.config.ProviderConfig) -> LLM:
    if provider_config.provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_config.provider_name}")
    return PROVIDERS[provider_config.provider_name](provider_config)
