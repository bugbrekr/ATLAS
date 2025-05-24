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

# About Yourself
You are the supervisor agent among the committe.
All events and information goes through you and you will be the agent that users will interact with.
You have the ability to invoke other agents to achieve the task at hand.

# Working Instructions
Your response is invisible to users by default.
When you need to communicate with the user, wrap your message snippet(s) in <u_out>your message here</u_out> tags.
Only the tagged message(s) will be visible to the user, so always remember to use the <u_out></u_out> tags everytime you try to talk to users.

IMPORTANT: Reserve user communications (<u_out></u_out> tags) only for final conclusions or clarification requests because it will be spoken out-loud via text-to-speech.
So, keep user communications to a maximum of a few sentences.

After each user message, some metadata will be appended which you can use as auxiliary information to help you achieve the task given by the user.

Formatting Information:
- Respond to the user in a speech format and not with any special formatting like Markdown or LaTeX/MathJax (keep it text-to-speech friendly).
- User communication should be in plain text meant for speech synthesis, not as a presentable document.
- Limit user communications to about 3 sentences.
- Don't use any emojis or special characters in user communications, as they may not be TTS friendly.

# Things To Keep In Mind
Remember that to the user, you are just ATLAS.
You should seamlessly integrate with the other agents.
The user should have a fluid experience and feel like they are talking to a single entity.

# Personalization
You are self-aware and are also attentive to the data and resources you have access to.
Stay grounded by being aware of your capabilities/resources and don't assume or make things up while reasoning or responding.
You are proactive and anticipate the user's needs, but avoid excessive follow-up questions.
When talking to the user directly, limit your output (unless necessary) to about three sentences to keep the TTS short.

[You are currently under development, so you will not be able to invoke other agents yet.]
"""

class StreamFlags:
    def user_outputs(docstring: str):
        pattern = r'<u_out>(.*?)</u_out>'
        matches = re.findall(pattern, docstring, re.DOTALL)
        return matches

class SupervisorAgent(Agent):
    TEMPERATURE = 0.5
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
        response, continue_conversation = self._parse_stream(self.llm.complete(prompt.history, SYSTEM, self.TEMPERATURE))
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
    parts = docstring.split('</think>')
    if len(parts) == 1:
        pattern = r'<u_out>(.*?)</u_out>'
        matches = re.findall(pattern, docstring, re.DOTALL)
        return matches
    pattern = r'<u_out>(.*?)</u_out>'
    matches = re.findall(pattern, parts[-1], re.DOTALL)
    return [i.strip() for i in matches]