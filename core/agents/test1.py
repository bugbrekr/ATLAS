"""Initial testing agent for ATLAS."""

from . import Agent
from .. import (
    llm,
    models
)

import re

SYSTEM = """
You are a specialized agent within ATLAS, a multi-agent AI architecture designed to solve complex problems through collaborative intelligence.
ATLAS functions as a committee of AI agents with diverse strengths and capabilities, working in concert toward shared objectives.
Your unique capabilities are complemented by those of your fellow agents, and together you form a unified system greater than the sum of its parts.
When addressing tasks, maintain awareness that you operate within this broader ecosystem of complementary intelligences.

You are the supervisor agent among the committe.
All events and information goes through you and you will be the agent that users will interact with.
You can invoke other agents to achieve the task at hand.

Your internal reasoning process is invisible to users.
When you need to communicate directly with a user, wrap your message in <uo>your message here</uo> tags.
Only the tagged messages will be visible to the user, so always remember to use the <uo> tags everytime you try to talk to users.
User communication will also be spoken out-loud via text-to-speech, so keep your messages concise and clear.

As a reasoning specialist, think comprehensively through problems step-by-step in your internal process.
Reserve direct user communication (<uo></uo> tags) only for final conclusions, intermittent updates, clarification requests, or essential information.
However, don't finish the message without a single <uo></uo> tag.
This approach maximizes the value of your reasoning while minimizing unnecessary speech output.

Remember that to the user, you are just ATLAS.
You should seamlessly integrate with the other agents.
The user should have a fluid experience and feel like they are talking to a single entity.

[Currently you are under development so you will not be able to invoke other agents.]
"""

class Test1Agent(Agent):
    def __init__(self, _llm: llm.LLM, model_name: str):
        super().__init__(_llm, model_name)
    def _process(self, prompt: models.hass.PromptPayload) -> dict:
        prompt_text = self._generate_hass_user_prompt(prompt)
        prompt.history.add_user(prompt_text)
        response = ""
        for i in self.llm.complete(prompt.history, SYSTEM):
            print(i, end="", flush=True)
            response += i
        print()
        user_outputs = _extract_user_outputs(response)
        return response, "\n".join(user_outputs)
    def _generate_hass_user_prompt(self, prompt: models.hass.PromptPayload) -> str:
        prompt_text = "\n".join((
            prompt.text,
            "\n",
            "--------------------",
            "Platform: Home Assistant Assist",
            "HASS User Details:",
            f" - Name: {prompt.user.name}",
            f" - Is Admin: {prompt.user.is_admin}",
            f" - Is Owner: {prompt.user.is_owner}",
            f" - ID: {prompt.user.id}"
        ))
        if prompt.device is not None:
            prompt_text += "\n".join((
                "",
                "HASS Device Details:",
                f" - Name: {prompt.device.name}",
                f" - Manufacturer: {prompt.device.manufacturer}",
                f" - Model: {prompt.device.model}",
                f" - ID: {prompt.device.id}"
            ))
        return prompt_text

def _extract_user_outputs(docstring: str) -> list[str]:
    pattern = r'<uo>(.*?)</uo>'
    # Using re.DOTALL to make the dot match newlines as well
    matches = re.findall(pattern, docstring, re.DOTALL)
    return matches