from bisect import bisect
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, SQLModel, ARRAY, Integer, Relationship, JSON
from sqlalchemy.sql.schema import Column


class Platform(Enum):
    TELEGRAM = "telegram"


TELEGRAM = Platform.TELEGRAM


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    timestamp: datetime
    platform: Platform


# class ChatUserLink(SQLModel, table=True):
#     chat_id: int = Field(foreign_key="chat.id", primary_key=True)
#     user_id: int = Field(foreign_key="user.id", primary_key=True)


# class Chat(SQLModel, table=True):
#     id: int = Field(primary_key=True)
#     users: List["User"] = Relationship(
#         back_populates="accessible_chats", link_model=ChatUserLink
#     )
#     platform: Platform


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    accessible_chats: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    # accessible_chats: List[Chat] = Relationship(
    #     back_populates="users", link_model=ChatUserLink
    # )
    platform: Platform

    def add_chat(self, id: int) -> None:
        ind = bisect(self.accessible_chats, id)
        if not (ind > 0 and self.accessible_chats[ind - 1] == id):
            # otherwise list is not updated in the db
            self.accessible_chats = list(self.accessible_chats)
            self.accessible_chats.insert(ind, id)
