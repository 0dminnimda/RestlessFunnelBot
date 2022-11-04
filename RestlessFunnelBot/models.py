from __future__ import annotations

from bisect import bisect
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, List, Optional, cast

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.schema import Column
from sqlmodel import JSON, Field, Relationship, SQLModel


def model_attr(attr: Any) -> InstrumentedAttribute:
    return cast(InstrumentedAttribute, attr)


TZ_UTC = timezone.utc
TZ_MOSCOW = timezone(timedelta(hours=3))


def to_moscow_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=TZ_UTC).astimezone(TZ_MOSCOW)


def from_moscow_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=TZ_MOSCOW).astimezone(TZ_UTC)


class Platform(Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    VK = "vk"


TELEGRAM = Platform.TELEGRAM
DISCORD = Platform.DISCORD
VK = Platform.VK


class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: Platform


class Message(BaseModel, table=True):
    text: str
    timestamp: datetime
    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship()
    chat_id: int = Field(foreign_key="chat.id")
    chat: Chat = Relationship()


NAME_SEPARATOR = chr(1)


class Chat(BaseModel, table=True):
    target_id: int
    name: str

    @staticmethod
    def generate_name(name: str, *names: str) -> str:
        return NAME_SEPARATOR.join((name,) + names)

    def represent_name(self, sep: str) -> str:
        return self.name.replace(NAME_SEPARATOR, sep)


class User(BaseModel, table=True):
    target_id: int
    access_id: Optional[int]
    accessible_chats: List[int] = Field(default_factory=list, sa_column=Column(JSON))

    def add_chat(self, chat: Chat) -> None:
        assert chat.id is not None
        ind = bisect(self.accessible_chats, chat.id)
        if not (ind > 0 and self.accessible_chats[ind - 1] == chat.id):
            # otherwise list is not updated in the db
            self.accessible_chats = list(self.accessible_chats)
            self.accessible_chats.insert(ind, chat.id)


Message.update_forward_refs()
Chat.update_forward_refs()
User.update_forward_refs()
