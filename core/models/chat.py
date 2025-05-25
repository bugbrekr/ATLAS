"""Models for chat messages."""

import datetime
from dataclasses import dataclass, InitVar
from typing import Union
from . import chat

@dataclass
class Message:
    content: str

@dataclass
class UserMessage(Message):
    role: InitVar = "user"
    content: str

@dataclass
class ToolMessage(Message):
    role: InitVar = "tool"
    content: str
    tool_call_id: str = ""

@dataclass
class AssistantMessage(Message):
    role: InitVar = "assistant"
    content: str
    tts_text: str = None
    def __init__(self, content: str, tts_text: str = None):
        if tts_text is None:
            tts_text = content
        self.content = content
        self.tts_text = tts_text

@dataclass
class History:
    history: list[UserMessage | AssistantMessage | ToolMessage] = None
    def __init__(self, history: list):
        self.history = []
        for msg in history:
            self.history.append(create_message(**msg))
    def add(self, message: Union[UserMessage, AssistantMessage, ToolMessage]):
        self.history.append(message)
    def add_user(self, content: str):
        self.history.append(create_message("user", content))
    def add_assistant(self, content: str, tts_text:str = None):
        self.history.append(create_message("assistant", content, tts_text=tts_text))
    def add_tool(self, content: str, tool_call_id: str = ""):
        self.history.append(create_message("tool", content, tool_call_id=tool_call_id))
    def to_messages(self, i: int = None) -> list[dict]:
        history = []
        for message in list(reversed(self.history))[:i]:
            d = {
                "role": message.role,
                "content": message.content
            }
            if isinstance(message, ToolMessage):
                d["tool_call_id"] = message.tool_call_id
            history.append(d)
        return list(reversed(history))

def create_message(
        role: str, 
        content: str, 
        tts_text: str = None,
        tool_call_id: str = ""
    ) -> Union[UserMessage, AssistantMessage, ToolMessage]:
    match role:
        case "user":
            return UserMessage(content=content)
        case "assistant":
            return AssistantMessage(content=content, tts_text=tts_text)
        case "tool":
            return ToolMessage(content=content, tool_call_id=tool_call_id)
        case _:
            raise ValueError(f"Invalid role: {role}")
