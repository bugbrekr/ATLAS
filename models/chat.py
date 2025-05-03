from dataclasses import dataclass
from typing import Union

@dataclass
class Message:
    content: str
        

@dataclass
class UserMessage(Message):
    pass

@dataclass
class AssistantMessage(Message):
    pass

def create_message(role: str, content: str) -> Union[UserMessage, AssistantMessage]:
    match role:
        case "user":
            return UserMessage(content)
        case "assistant":
            return AssistantMessage(content)
        case _:
            raise ValueError(f"Invalid role: {role}")
