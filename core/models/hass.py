"""Models for Home Assistant."""

import datetime
from dataclasses import dataclass
from typing import Union
from . import chat
from .chat import (
    UserMessage,
    AssistantMessage,
    History,
    create_message,
)

@dataclass
class User:
    name: str = None
    is_admin: bool = None
    is_owner: bool = None
    id: str = None
    def __init__(self, user: dict):
        if not isinstance(user, dict): raise TypeError("`user` must be `dict`")
        self.name = user.get("name")
        self.is_admin = user.get("is_admin")
        self.is_owner = user.get("is_owner")
        self.id = user.get("id")

@dataclass
class Device:
    name: str = None
    manufacturer: str = None
    model: str = None
    id: str = None
    def __init__(self, device: dict):
        if not isinstance(device, dict): raise TypeError("`device` must be `dict`")
        self.name = device.get("name")
        self.manufacturer = device.get("manufacturer")
        self.device = device.get("model")
        self.id = device.get("id")

@dataclass
class PromptPayload:
    text: str = None
    dt: datetime.datetime = None
    history: History = None
    conversation_id: str = None
    user: User = None
    device: Device = None
    message: Union[UserMessage, AssistantMessage] = None
    def __init__(self, payload: dict):
        if not isinstance(payload, dict): raise TypeError("`payload` must be `dict`")
        self.text = payload.get("input_text")
        self.dt = datetime.datetime.fromtimestamp(payload.get("timest", 0))
        self.history = History(payload.get("history"))
        self.conversation_id = payload.get("conversation_id")
        self.user = User(payload.get("user_info"))
        self.device = Device(payload.get("device_info")) if payload.get("device_info") else None
        self.message = create_message("user", self.text)

def generate_response_payload(history: History, content:str = None, tts_text: str = None, continue_conversation: bool = False) -> dict:
    """
    Generates response payload from history.
    If last message in history is not an `AssistantMessage`, one will be added from `content` and `tts_text`.
    """
    if not isinstance(history.history[-1], AssistantMessage):
        if content is None:
            raise ValueError("Last added message in history must be `AssistantMessage` or `content` must be provided.")
        if content is None:
            raise ValueError("`content` must be provided if last message in history is not `AssistantMessage`")
        if tts_text is None:
            raise ValueError("`tts_text` must be provided if last message in history is not `AssistantMessage`")
        history.add_assistant(content, tts_text)
    return {
        "tts_text": tts_text or history.history[-1].tts_text,
        "new_history": history.to_messages(),
        "continue_conversation": continue_conversation
    }