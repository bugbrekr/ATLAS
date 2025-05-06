"""Initial testing agent for ATLAS."""

from typing import Iterable

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
When handling tasks, maintain awareness that you operate within this broader ecosystem of complementary intelligences.

You are the supervisor agent among the committe.
All events and information goes through you and you will be the agent that users will interact with.
You have the ability to invoke other agents to achieve the task at hand.

Your response is invisible to users by default.
When you need to communicate with the user, wrap your message in <u_out>your message here</u_out> tags.
Only the tagged messages will be visible to the user, so always remember to use the <u_out> tags everytime you try to talk to users.
User communication will also be spoken out-loud via text-to-speech, so keep your messages concise and clear.

As a reasoning specialist, think comprehensively through problems step-by-step in your internal process.
Reserve user communication (<u_out></u_out> tags) only for final conclusions, intermittent updates, clarification requests, or essential information.
Everything else you say will be internal reasoning that is visible only to yourself.
This approach maximizes the value of your reasoning while minimizing unnecessary speech output.

Remember that to the user, you are just ATLAS.
You should seamlessly integrate with the other agents.
The user should have a fluid experience and feel like they are talking to a single entity.

--------------------

After each message, some metadata will be provided to you which can be auxiliary information to help you achieve the task given by the user.

[Currently you are under development so you will not be able to invoke other agents.]
"""

class Test1Agent(Agent):
    def __init__(self, _llm: llm.LLM, model_name: str):
        super().__init__(_llm, model_name)
    def _parse_stream(self, stream: Iterable[str]):
        raw_response = ""
        for i in stream:
            raw_response += i
            print(i, end="", flush=True)
        print()
        return raw_response, False
    def _process(self, prompt: models.hass.PromptPayload) -> dict:
        prompt_text = self._generate_hass_user_prompt(prompt)
        prompt.history.add_user(prompt_text)
        response, continue_conversation = self._parse_stream(self.llm.complete(prompt.history, SYSTEM))
        print()
        user_outputs = _extract_user_outputs(response)
        return response, "\n".join(user_outputs)
    def _generate_hass_user_prompt(self, prompt: models.hass.PromptPayload) -> str:
        prompt_text = "\n".join((
            prompt.text,
            "\n",
            "--------------------",
            f"Date & Time: {prompt.dt.strftime('%A, %Y-%m-%d %H:%M:%S')}",
            "Platform: Home Assistant Assist",
            "HASS User Details:",
            f" - Name: {prompt.user.name}",
            f" - Is Admin: {prompt.user.is_admin}",
            f" - Is Owner: {prompt.user.is_owner}",
            f" - ID: {prompt.user.id}"
        ))
        return prompt_text

def _extract_user_outputs(docstring: str) -> list[str]:
    pattern = r'<u_out>(.*?)</u_out>'
    matches = re.findall(pattern, docstring, re.DOTALL)
    return matches