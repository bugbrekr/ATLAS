"""High-level API for ATLAS."""

from . import (
    models,
    agents
)

class ATLAS:
    def __init__(self, config: models.config.Config):
        self.config = config
        self.agents = agents.Agents(config.agent_backends)
    def process_hass_user(self, prompt: models.hass.PromptPayload) -> dict:
        continue_conversation = self.agents.supervisor.process(prompt)
        return models.hass.generate_response_payload(
            history=prompt.history,
            continue_conversation=continue_conversation
        )
