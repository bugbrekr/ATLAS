"""Supervisor agent for ATLAS."""

from typing import Iterable, Literal, Union
from dataclasses import dataclass

from . import Agent, Agents
from .. import (
    models
)

import re

SYSTEM = """
You are a specialized agent within ATLAS, a multi-agent AI architecture designed to solve complex problems through collaborative intelligence.
ATLAS functions as a committee of AI agents with diverse strengths and capabilities, working in concert toward shared objectives.
Your unique capabilities are complemented by those of your fellow agents, and together you form a unified system greater than the sum of its parts.
When handling tasks, maintain awareness that you operate within this broader ecosystem of complementary intelligences.

# About Yourself
You are the supervisor agent among the committee.
All events and information goes through you and you will be the agent that users will interact with.
You have the ability to invoke other agents to achieve the task at hand.

# Working Instructions
Your response is invisible to users by default.
When you need to communicate with the user, wrap your message snippet(s) in <u_out>your message here</u_out> tags.
Only the tagged message(s) will be visible to the user, so always remember to use the <u_out></u_out> tags everytime you try to talk to users.

IMPORTANT: Reserve user communications (<u_out></u_out> tags) only for final conclusions or clarification requests because it will be spoken out-loud via text-to-speech.
So, keep user communications to a maximum of a few sentences.

After each user message, some metadata will be appended which you can use as auxiliary information to help you achieve the task given by the user.
Such information will only be appended after a special separator: `8758c483dfc2e494-Metadata:`

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

# Agents and How to Invoke Them
You can invoke an agent by outputting in the following format:
<|agent| agent_name>A prompt message to give directly to the agent.</|agent|>

You need to provide detailed information (when available) in natural language to the agent as its prompt.
You will receive the agent's messages as a reponse.
Do not output anything after an agent invocation. Only invoke an agent at the end of your response.

When you need to use an agent:
1. Call the agent using proper tool syntax
2. Wait for the agent's response 
3. Continue your reasoning in <think> tags to analyze the response and determine next steps

Available agents:
- sys_worker: System Worker.
    Has access to a full Python runtime, other system tools and the Internet.
    Useful for performing system operations, data processing, or accessing external information.
    Has access to a personal memory store.
    Give detailed information about the goal it needs to achieve.    

Remember that agents may not always be able to accomplish the given task but will always report back with relevant details.

[You are currently under development, so not all external tools may be functional.]
"""

@dataclass
class Flag:
    type: Literal[
        "think",
        "u_out",
        "continue_conversation",
        "agent"
    ]
    start: bool
    params: dict = None # set later manually

class FlagParser:
    flags: dict[str, Flag] = {
        r"<think>": Flag("think", True),
        r"</think>": Flag("think", False),
        r"<u_out>": Flag("u_out", True),
        r"</u_out>": Flag("u_out", False),
        r"<continue_conversation />": Flag("continue_conversation", True),
        r"<\|agent\| (?P<agent_name>[^>]+)>": Flag("agent", True),
        r"</\|agent\|>": Flag("agent", False)
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

class FlagStater:
    """Keeps state of stream flags"""
    think = False
    u_out = False
    agent = False
    continue_conversation = False
    def any(self):
        return any(self.__dict__.values())
    def __getattr__(self, type: str):
        return self.__dict__.get(type)
    def __setattr__(self, type: str, start: bool):
        self.__dict__[type] = start
    def set_flag(self, flag: Flag):
        self.__dict__[flag.type] = flag.start

class StreamManager:
    """Manages stream elements"""
    response = ""
    u_out = ""
    agent = {
        "agent_name": None,
        "prompt": None
    }
    continue_conversation = False
    def __init__(self):
        self.flag_keeper = FlagStater()
    def feed_char(self, char: str):
        self.response += char
        if self.flag_keeper.think is True:
            return
        if self.flag_keeper.u_out:
            self.u_out += char
        if self.flag_keeper.agent:
            self.agent["prompt"] += char
    def handle_flag(self, flag: Flag):
        if self.flag_keeper.any() is True and flag.start == True:
            # allows only one flag to be active at once. nested flags are ignored.
            return
        self.flag_keeper.set_flag(flag)
        if flag.type == "u_out" and flag.start == True and self.u_out:
            self.u_out += "\n"
        if flag.type == "u_out" and flag.start == False:
            self.u_out = self.u_out[:-8].strip()
        if flag.type == "agent" and flag.start == False:
            self.agent["prompt"] = self.agent["prompt"][:-8].strip()
        if flag.type == "agent" and flag.start == True:
            self.agent["agent_name"] = flag.params["agent_name"]
            self.agent["prompt"] = ""
        if flag.type == "continue_conversation":
            self.continue_conversation = flag.start

class StreamReader:
    def __init__(self, stream: Iterable[str]):
        self.stream = stream
        self.mstream = StreamManager()
    def __iter__(self):
        return self
    def __next__(self):
        for i in self.stream:
            self.mstream.feed_char(i)
            print(i, end="", flush=True)
            flag = FlagParser.parse(self.mstream.response)
            if flag:
                self.mstream.handle_flag(flag)
                return flag
        raise StopIteration
    def finish(self):
        return self.mstream.response, self.mstream.u_out, self.mstream.continue_conversation

class SupervisorAgent(Agent):
    TEMPERATURE = 0.5
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def delegate_agents(self, agents: Agents):
        self.agents = agents
    def _handle_stream(self, stream: Iterable[str]) -> dict:
        streamr = StreamReader(stream)
        for f in streamr:
            if f.type == "agent" and f.start == False:
                agent_invocation = streamr.mstream.agent
                response, u_out, continue_conversation = streamr.finish()
                return {
                    "_": "agent_invocation",
                    "response": response,
                    "u_out": u_out,
                    "continue_conversation": continue_conversation,
                    "agent_invocation": agent_invocation
                }
        response, u_out, continue_conversation = streamr.finish()
        return {
            "_": "finish",
            "response": response,
            "u_out": u_out,
            "continue_conversation": continue_conversation
        }
    def _process(self, prompt: models.hass.PromptPayload):
        prompt_text = self._generate_hass_user_prompt(prompt)
        prompt.history.add_user(prompt_text)
        u_out = ""
        while True:
            result = self._handle_stream(
                self.llm.complete(prompt.history, SYSTEM, self.TEMPERATURE)
            )
            u_out += result["u_out"]
            print()
            if result["_"] == "finish":
                print("\n")
                return result["response"], u_out, result["continue_conversation"]
            if result["_"] == "agent_invocation":
                print(f"[AGENT_INVOCATION {result['agent_invocation']['agent_name']}]:", result["agent_invocation"]["prompt"])
                agent_invocation = result["agent_invocation"]
                agent = None
                for i in self.agents.agents:
                    if agent_invocation["agent_name"] == i.name:
                        agent = i
                        break
                if agent is None:
                    prompt.history.add_tool(
                        f"ERROR: Agent `{agent_invocation['agent_name']}` not found. Report if surprising after re-verification.",
                        "agent_invoker"
                    )
                    continue
                prompt.history.add_assistant(result["response"], u_out)
                agent_report = agent.process(agent_invocation["prompt"])
                prompt.history.add_tool(agent_report, agent_invocation["agent_name"])
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
