"""Config wrapper."""

from dataclasses import dataclass
import toml
import os

@dataclass
class ProviderConfig:
    name: str
    provider_name: str
    api_key: str

@dataclass
class ProvidersConfig:
    cerebras: ProviderConfig = None

@dataclass
class AgentConfig:
    name: str
    provider_config: ProviderConfig
    model_name: str

@dataclass
class Config:
    providers: ProvidersConfig
    agent_backends: list[AgentConfig]
    def __init__(self, config_folder: str):
        llm_providers_file = os.path.join(config_folder, "llm_providers.toml")
        self.providers = ProvidersConfig()
        llm_providers = self._load_config(llm_providers_file)
        for k,v in llm_providers.items():
            setattr(self.providers, k, ProviderConfig(k, v.get("provider"), v.get("api_key")))
        
        agent_backends_file = os.path.join(config_folder, "agent_backends.toml")
        self.agent_backends = []
        agent_backends = self._load_config(agent_backends_file)
        for k,v in agent_backends.items():
            agent_config = AgentConfig(
                k,
                self.providers.__getattribute__(v.get("provider")),
                v.get("model_name")
            )
            self.agent_backends.append(agent_config)
    def _load_config(self, config_file: str):
        with open(config_file, "r") as f:
            return toml.load(f)
