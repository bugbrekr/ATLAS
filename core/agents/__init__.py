"""Bunch of ATLAS agents. Expect no consistency or structure between each agent."""

from dataclasses import dataclass

from .. import (
    models,
    llm
)

class Agent:
    """An abstract base class for all ATLAS agents. For __some__ consistency."""
    def __init__(self, name: str, _llm: llm.LLM, model_name: str):
        self.name = name
        self.llm = _llm
        self.llm.set_model_name(model_name)
    def process(self, prompt: models.hass.PromptPayload) -> bool:
        """Process the prompt and return a response. Returns `continue_conversation`"""
        resp = self._process(prompt)
        if isinstance(resp, tuple):
            resp_text = resp[0]
            tts_text = resp[1]
            continue_conversation = resp[2] if len(resp) > 2 else False
            prompt.history.add_assistant(resp_text, tts_text)
            return continue_conversation
        prompt.history.add_assistant(resp)
        return resp

@dataclass
class Agents:
    agents: list[Agent]
    def __init__(self, agents: list[Agent]):
        self.agents = agents
        for agent in agents:
            setattr(self, agent.name, agent)

from . import (
    supervisor,
    sys_worker
)

_AGENTS_LIST: dict[str, Agent] = {
    "supervisor": supervisor.SupervisorAgent,
    "sys_worker": sys_worker.SysWorkerAgent
}

@dataclass
class ConfigAgents(Agents):
    supervisor: supervisor.SupervisorAgent
    sys_worker: sys_worker.SysWorkerAgent
    def __init__(self, agent_configs: list[models.config.AgentConfig]):
        super().__init__([factory(i) for i in agent_configs])

def factory(agent_config: models.config.AgentConfig) -> Agent:
    _llm = llm.factory(agent_config.provider_config)
    if agent_config.name not in _AGENTS_LIST:
        raise ValueError(f"Unknown agent: {agent_config.name}")
    return _AGENTS_LIST[agent_config.name](agent_config.name, _llm, agent_config.model_name)
