from __future__ import annotations

from bisect import bisect
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, List, Optional, cast

from sqlalchemy.sql.elements import ColumnClause
from sqlalchemy.sql.schema import Column
from sqlmodel import JSON, Field, Relationship, SQLModel


# instead of sqlmodel.col()
def col(attr: Any) -> ColumnClause:
    # ColumnClause, Column, InstrumentedAttribute
    return cast(ColumnClause, attr)


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


class PlatformModel(BaseModel):
    target_id: int
    platform: Platform


class Message(PlatformModel, table=True):
    text: str
    timestamp: datetime
    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship()
    chat_id: int = Field(foreign_key="chat.id")
    chat: Chat = Relationship()


NAME_SEPARATOR = chr(1)


class Chat(PlatformModel, table=True):
    name: str

    @staticmethod
    def generate_name(name: str, *names: str) -> str:
        return NAME_SEPARATOR.join((name,) + names)

    def represent_name(self, sep: str) -> str:
        return self.name.replace(NAME_SEPARATOR, sep)


def _unique_append(lst: List[int], item: int) -> List[int]:
    ind = bisect(lst, item)
    if not (ind > 0 and lst[ind - 1] == item):
        # otherwise list is not updated in the db
        lst = list(lst)
        lst.insert(ind, item)
    return lst


class User(PlatformModel, table=True):
    chats: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    connection_id: int = Field(foreign_key="connecteduser.id")
    connection: ConnectedUser = Relationship()

    def add_chat(self, chat: Chat) -> None:
        assert chat.id is not None
        self.chats = _unique_append(self.chats, chat.id)
        self.connection.chats = _unique_append(self.connection.chats, chat.id)


class ConnectedUser(BaseModel, table=True):
    chats: List[int] = Field(default_factory=list, sa_column=Column(JSON))

    def add_chats_from(self, other: ConnectedUser) -> None:
        self.chats = sorted(set(self.chats).union(other.chats))


Message.update_forward_refs()
Chat.update_forward_refs()
User.update_forward_refs()
ConnectedUser.update_forward_refs()
