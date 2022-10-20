from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class Platform(Enum):
    TELEGRAM = "telegram"


# try to use sqlmodel
@dataclass
class Message:
    text: str
    timestamp: datetime
    platform: Platform


def save_message(message: Message) -> None:
    print(message)
    pass  # TODO
