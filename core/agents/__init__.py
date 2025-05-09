"""Bunch of ATLAS agents. Expect no consistency or structure between each agent."""

from dataclasses import dataclass

from .. import (
    models,
    llm
)

class Agent:
    """An abstract base class for all ATLAS agents. For __some__ consistency."""
    def __init__(self, _llm: llm.LLM, model_name: str):
        self.llm = _llm
        self.llm.set_model_name(model_name)
    def process(self, prompt: models.hass.PromptPayload) -> str:
        """Process the prompt and return a response."""
        resp = self._process(prompt)
        if isinstance(resp, tuple):
            resp_text = resp[0]
            tts_text = resp[1]
            prompt.history.add_assistant(resp_text, tts_text)
            return resp_text
        prompt.history.add_assistant(resp)
        return resp

from . import test1

_AGENTS_LIST: dict[str, Agent] = {
    "test1": test1.Test1Agent,
}

@dataclass
class Agents:
    test1: test1.Test1Agent
    def __init__(self, agent_configs: list[models.config.AgentConfig]):
        for agent_config in agent_configs:
            if agent_config.name not in _AGENTS_LIST:
                raise ValueError(f"Unknown agent: {agent_config.name}")
            setattr(self, agent_config.name, factory(agent_config))

def factory(agent_config: models.config.AgentConfig) -> Agent:
    _llm = llm.factory(agent_config.provider_config)
    if agent_config.name not in _AGENTS_LIST:
        raise ValueError(f"Unknown agent: {agent_config.name}")
    return _AGENTS_LIST[agent_config.name](_llm, agent_config.model_name)
