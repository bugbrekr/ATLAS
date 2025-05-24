"""Initial testing agent for ATLAS."""

from typing import Iterable, Literal, Union
from dataclasses import dataclass

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
Such information will only be after a special separator: `8758c483dfc2e494-Metadata:`

Formatting Information:
- All user communication must be in plain-text, text-to-speech-friendly format. This means, you must not use any formatting or highlighting whatsoever.
- Limit user communications to about 3 sentences.
- Don't use any emojis or special characters in user communications, as they may not be TTS friendly.

At the end of your message, if you are expecting a follow-up input from the user, use the following flag to automatically restart speech-to-text: <continue_conversation />
Do so only when you are asking the user a question, don't if you are just giving an answer.

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

@dataclass
class Flag:
    type: Literal[
        "think",
        "u_out",
        "continue_conversation"
    ]
    start: bool
    params: dict = None # set later manually

class FlagParser:
    flags: dict[str, Flag] = {
        r"<think>": Flag("think", True),
        r"</think>": Flag("think", False),
        r"<u_out>": Flag("u_out", True),
        r"</u_out>": Flag("u_out", False),
        r"<continue_conversation />": Flag("continue_conversation", True)
    }
    
    @classmethod
    def parse(self, docstr: str) -> Union[Flag, None]:
        """
        Go through each flag trigger, check if the last match is at the end.
        """
        for pattern, flag in self.flags.items():
            matches = list(re.finditer(pattern, docstr))
            if not matches:
                continue
            last_match = matches[-1]
            match_end = last_match.span()[1]
            if match_end == len(docstr):
                flag.params = last_match.groupdict()
                return flag
        return None

class FlagKeeper:
    """Certain stream-handling necessary flag data"""
    thinking: bool = False
    u_out: bool = False

class StreamReader:
    def __init__(self, stream: Iterable[str]):
        self.stream = stream
    def __iter__(self):
        self.response = ""
        self.u_out = ""
        self.continue_conversation = False
        self.finish_stream = True
        self.flag_keeper = FlagKeeper()
        return self
    def __next__(self):
        for i in self.stream:
            self.response += i
            print(i, end="", flush=True)
            if self.flag_keeper.u_out:
                self.u_out += i
            flag = FlagParser.parse(self.response)
            if not flag:
                continue
            match flag.type:
                case "think":
                    self.flag_keeper.thinking = flag.start
                case "u_out":
                    if not self.flag_keeper.thinking:
                        self.flag_keeper.u_out = flag.start
                        if flag.start is False:
                            # remove the trailing </u_out>
                            self.u_out = self.u_out[:-8]
                case "continue_conversation":
                    if not self.flag_keeper.thinking and not self.flag_keeper.u_out:
                        self.continue_conversation = flag.start
            return flag
        raise StopIteration
    def finish(self):
        return self.response, self.u_out, self.finish_stream, self.continue_conversation

class SupervisorAgent(Agent):
    TEMPERATURE = 0.5
    def __init__(self, _llm: llm.LLM, model_name: str):
        super().__init__(_llm, model_name)
    def _handle_stream(self, stream: Iterable[str]):
        response = ""
        u_outs = []
        while True:
            streamr = StreamReader(stream)
            for f in streamr:
                print(f)
            _response, _u_out, _finish_stream, _continue_conversation = streamr.finish()
            response += _response
            u_outs.append(_u_out)
            if _finish_stream:
                break
        return response, "\n".join(u_outs), _continue_conversation
    def _process(self, prompt: models.hass.PromptPayload) -> dict:
        prompt_text = self._generate_hass_user_prompt(prompt)
        prompt.history.add_user(prompt_text)
        response, u_out, continue_conversation = self._handle_stream(
            self.llm.complete(prompt.history, SYSTEM, self.TEMPERATURE)
        )
        print()
        return response, u_out, continue_conversation
    def _generate_hass_user_prompt(self, prompt: models.hass.PromptPayload) -> str:
        prompt_text = "\n".join((
            prompt.text,
            "\n",
            "8758c483dfc2e494-Metadata:",
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