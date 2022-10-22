from bisect import bisect
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy.sql.schema import Column
from sqlmodel import JSON, Field, SQLModel


class Platform(Enum):
    TELEGRAM = "telegram"


TELEGRAM = Platform.TELEGRAM


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    timestamp: datetime
    platform: Platform


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    accessible_chats: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    platform: Platform

    def add_chat(self, id: int) -> None:
        ind = bisect(self.accessible_chats, id)
        if not (ind > 0 and self.accessible_chats[ind - 1] == id):
            # otherwise list is not updated in the db
            self.accessible_chats = list(self.accessible_chats)
            self.accessible_chats.insert(ind, id)
