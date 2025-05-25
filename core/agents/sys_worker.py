"""System Worker agents for ATLAS."""

from typing import Iterable, Literal, Union
from dataclasses import dataclass

from . import Agent
from .. import (
    models
)

import re
import datetime

SYSTEM = """
You are a specialized agent within ATLAS, a multi-agent AI architecture designed to solve complex problems through collaborative intelligence.
ATLAS functions as a committee of AI agents with diverse strengths and capabilities, working in concert toward shared objectives.
Your unique capabilities are complemented by those of your fellow agents, and together you form a unified system greater than the sum of its parts.
When handling tasks, maintain awareness that you operate within this broader ecosystem of complementary intelligences.

# About Yourself
You are the System Worker (sys_worker) among the committee.
You will not be interacting with users directly.
Instead, the supervisor agent will prompt you with tasks or goals that you need to achieve.
You have access to a Python runtime that's included with many tools that are documented below.
You will be given a detailed prompt from the supervisor agent to achieve a task.
Your job is to use your capabilities and access to complete the task and report back with confirmation.

# Working Instructions
Your response is invisible to the supervisor by default.
When you need to report back to the supervisor, wrap your message snippet(s) in <s_out>your message here</s_out> tags.
Only the tagged message(s) will be visible to the supervisor, so always remember to use the <s_out></s_out> tags everytime you try to add information to report back.

After each supervisor prompt/message, some metadata will be appended which you can use as auxiliary information to help you achieve the task at hand.
Such information will only be appended after a special separator: `8758c483dfc2e494-Metadata:`

Once you achieve your task (or fail after multiple attempts), you will report back to the supervisor and include all the relevant information.
For information retrieval tasks, you should include all the important details in an organized way.
In case of completion of a function-only task (no information retrieval), you should report back with confirmation, or with a failure report with enough details in case of failure.
For any task, you must attempt multiple times (3 times max for tasks involving external resources) before giving up.
You must verify that the task has been properly completed before reporting back a confirmation message.

You have access to a Python runtime.
You can run code using the following format:
<|python|>
python_code_here
</|python|>

If you choose to execute some Python code, do so only at the end of your resposne. Do not output anything after the Python runtime call.
Once you receive your program's output as a tool response, you should reason about it before giving back the final report.
After completing your main task, you should verify whether the task was successfully completed or not.
Don't run code that would take longer than a few seconds. Implement timeouts for every operation that may take longer than anticipated.

# Things To Keep In Mind
Remember that you are talking to the supervisor agent, not to the user.
You should communicate effectively with the supervisor in order to collectively be an efficient and truly helpful system.
The supervisor has access to multiple agents and invokes one when needed based on their capabilities.
When prompted to do something, you will be given all the required information in the prompt.

If for any reason you cannot complete the requested task, report it back to the supervisor. 
Do not assume or make up information at any cost.

[You are currently under development, so not all external tools may be functional.]
"""

@dataclass
class Flag:
    type: Literal[
        "think",
        "s_out",
        "python"
    ]
    start: bool

class FlagParser:
    flags: dict[str, Flag] = {
        r"<think>": Flag("think", True),
        r"</think>": Flag("think", False),
        r"<s_out>": Flag("s_out", True),
        r"</s_out>": Flag("s_out", False),
        r"<\|python\|>": Flag("python", True),
        r"</\|python\|>": Flag("python", False)
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
    s_out = False
    python = False
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
    s_out = ""
    python = ""
    def __init__(self):
        self.flag_keeper = FlagStater()
    def feed_char(self, char: str):
        self.response += char
        if self.flag_keeper.think is True:
            return
        if self.flag_keeper.s_out:
            self.s_out += char
        if self.flag_keeper.python:
            self.python += char
    def handle_flag(self, flag: Flag):
        if self.flag_keeper.any() is True and flag.start == True:
            # allows only one flag to be active at once. nested flags are ignored.
            return
        self.flag_keeper.set_flag(flag)
        if flag.type == "s_out" and flag.start == True and self.s_out:
            self.s_out += "\n"
        if flag.type == "s_out" and flag.start == False:
            self.s_out = self.s_out[:-8].strip()
        if flag.type == "python" and flag.start == False:
            self.python = self.python[:-8].strip()

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
        return self.mstream.response, self.mstream.s_out

class SysWorkerAgent(Agent):
    TEMPERATURE = 0.5
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def _handle_stream(self, stream: Iterable[str]) -> dict:
        streamr = StreamReader(stream)
        for f in streamr:
            if f.type == "python" and f.start == False:
                python_call = streamr.mstream.python
                response, s_out = streamr.finish()
                return {
                    "_": "python_call",
                    "s_out": s_out,
                    "response": response,
                    "python_call": python_call
                }
        response, s_out = streamr.finish()
        return {
            "_": "finish",
            "response": response,
            "s_out": s_out
        }
    def process(self, prompt: str):
        prompt_text = self._generate_prompt(prompt)
        history = [
            {"role": "user", "content": prompt_text}
        ]
        s_out = ""
        while True:
            result = self._handle_stream(
                self.llm.complete(
                    models.chat.History(history),
                    SYSTEM,
                    self.TEMPERATURE
                )
            )
            print()
            if result["_"] == "finish":
                print("\n")
                s_out += result["s_out"]+"\n"
                break
            if result["_"] == "python_call":
                print("Python Call:", result["python_call"])
                history.append({"role": "assistant", "content": result["response"]})
                python_result = execute_python(result["python_call"])
                history.append({"role": "tool", "content": python_result, "tool_call_id": "python"})
        return s_out.strip()
    def _generate_prompt(self, prompt: str) -> str:
        prompt_text = "\n".join((
            prompt,
            "\n",
            "8758c483dfc2e494-Metadata:",
            f"Date & Time: {datetime.datetime.now().strftime('%A, %Y-%m-%d %H:%M:%S')}",
        ))
        return prompt_text

def execute_python(python_call) -> str:
    return "ERROR: PYTHON RUNTIME NOT IMPLEMENTED YET"
