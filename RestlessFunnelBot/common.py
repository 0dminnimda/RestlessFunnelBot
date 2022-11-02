from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .database import DataBase, make_db
from .mappers import map_model
from .messenger import answer_to, reply_to
from .models import Chat, Message, Platform, User, model_attr


TZ_UTC = timezone.utc
TZ_MOSCOW = timezone(timedelta(hours=3))
TIME_FORMAT = "%d %B %Y - %H:%M:%S (%Z)"


def to_moscow_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=TZ_UTC).astimezone(TZ_MOSCOW)


def from_moscow_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=TZ_MOSCOW).astimezone(TZ_UTC)


async def all_messages(db: DataBase, user: User) -> str:
    messages = []
    for msg in await db.read_all(Message):
        date = to_moscow_tz(msg.timestamp).strftime(TIME_FORMAT)
        messages.append(f"{msg.id}) {date}:\n{msg.text}\n")
    return "List of all messages\n" + "\n".join(messages)


CHAT_SEP = "/"


async def accessible_chats(db: DataBase, user: User) -> str:
    chats = await db.read_all(Chat, model_attr(Chat.id).in_(user.accessible_chats))
    names = [f"{i+1} {chat.represent_name(CHAT_SEP)}" for i, chat in enumerate(chats)]
    return "List of accessible chats\n" + "\n".join(names)


async def greet(db: DataBase, user: User):
    return (
        "Hi, I'm RestlessFunnelBot!\n"
        "I listen to others, and then I retell everything to you 🤗\n"
    )


replies = {
    "/list": all_messages,
    "/chats": accessible_chats,
    "/start": greet,
    "/help": greet,
}


async def reply_to_message(db: DataBase, in_msg: Any, msg: Message) -> None:
    reply = replies.get(msg.text)
    if reply is not None:
        await answer_to(in_msg, await reply(db, msg.author))


async def make_message(
    db: DataBase, in_msg: Any, chat: Any, author: Any, is_private: bool
) -> Message:
    fields = map_model(in_msg)

    chat = fields["chat"] = await db.read_or_create(Chat, **map_model(chat))
    fields["chat_id"] = chat.id

    author = fields["author"] = await db.read_or_create(User, **map_model(author))
    fields["author_id"] = author.id

    msg = db.create_no_add(Message, **fields)
    if not is_private:
        author.add_chat(chat)
        db.add(msg)
    return msg


async def handle_message(
    platform: Platform, in_msg: Any, chat: Any, author: Any, is_private: bool
) -> None:
    async with make_db(platform) as db:
        msg = await make_message(db, in_msg, chat, author, is_private)
        if is_private:
            await reply_to_message(db, in_msg, msg)
