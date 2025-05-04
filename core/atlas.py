"""High-level API for ATLAS."""

from . import (
    models,
    llm,
    agents
)

class ATLAS:
    def __init__(self, config: models.config.Config):
        self.config = config
        self.agents = agents.Agents(config.agent_backends)
    def process_hass_user(self, prompt: models.hass.PromptPayload) -> dict:
        self.agents.test1.process(prompt)
        return models.hass.generate_response_payload(prompt.history)
    
