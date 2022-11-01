from typing import Any, Optional

from .database import DataBase
from .mappers import map_model
from .models import Chat, Message, Platform, User, model_attr


async def list_messages(db: DataBase) -> str:
    messages = []
    for msg in await db.read_all(Message):
        messages.append("-" * 50 + f"\n{msg.id}: {msg.text}")
    return "List of all messages\n" + "\n\n".join(messages)


CHAT_SEP = "/"


async def list_accessible_chats(db: DataBase, user: User) -> str:
    chats = await db.read_all(Chat, model_attr(Chat.id).in_(user.accessible_chats))
    names = [f"{i+1} {chat.represent_name(CHAT_SEP)}" for i, chat in enumerate(chats)]
    return "List of accessible chats\n" + "\n".join(names)


async def make_message(db: DataBase, in_msg: Any, chat: Any, author: Any) -> Message:
    mod = map_model(in_msg)

    chat = mod["chat"] = await db.read_or_create(Chat, **map_model(chat))
    mod["chat_id"] = chat.id

    author = mod["author"] = await db.read_or_create(User, **map_model(author))
    mod["author_id"] = author.id

    author.add_chat(chat)

    return db.create_no_add(Message, **mod)

async def handle_new_message(db: DataBase, in_msg: Any) -> Optional[str]:
    msg = await make_message(db, in_msg)

    if msg.text.startswith("/list"):
        return await list_messages(db)

    if msg.text.startswith("/chats"):
        return await list_accessible_chats(db, msg.author)

    db.add(msg)
    return None
