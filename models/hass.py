import datetime
from dataclasses import dataclass
from typing import Union
from . import chat

@dataclass
class UserMessage(chat.UserMessage):
    pass

@dataclass
class AssistantMessage(chat.AssistantMessage):
    tts_text: str = None
    def __init__(self, content: str, tts_text: str = None):
        if tts_text is None:
            tts_text = content
        super().__init__(
            content = content
        )
        self.tts_text = tts_text

def create_message(role: str, content: str, tts_text: str = None) -> Union[UserMessage, AssistantMessage]:
    match role:
        case "user":
            return UserMessage(content = content)
        case "assistant":
            return AssistantMessage(content = content, tts_text = tts_text)
        case _:
            raise ValueError(f"Invalid role: {role}")


@dataclass
class History:
    history: list = None
    def __init__(self, history: list):
        self.history = []
        for msg in history:
            self.history.append(create_message(**msg))
    def generate_history(self):
        pass

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
    def __init__(self, payload: dict):
        if not isinstance(payload, dict): raise TypeError("`payload` must be `dict`")
        self.text = payload.get("input_text")
        self.dt = datetime.datetime.fromtimestamp(payload.get("timest", 0))
        self.history = History(payload.get("history"))
        self.conversation_id = payload.get("conversation_id")
        self.user = User(payload.get("user_info"))
        self.device = Device(payload.get("device_info")) if payload.get("device_info") else None
