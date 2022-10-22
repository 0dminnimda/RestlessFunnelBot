from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class Platform(Enum):
    TELEGRAM = "telegram"


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # id: int = Field(primary_key=True)
    text: str
    timestamp: datetime
    platform: Platform
