import re
from typing import Any, Dict, Optional, Tuple, Callable, Awaitable

from .bot import Bot, bot
from .database import DataBase, make_db
from .mappers import map_model
from .models import Chat, Message, Platform, User, model_attr, to_moscow_tz

TIME_FORMAT = "%d %B %Y - %H:%M:%S (%Z)"


@bot.command("list")
async def all_messages(bot: Bot, text: str) -> None:
    messages = []
    for msg in await bot.db.read_all(Message):
        date = to_moscow_tz(msg.timestamp).strftime(TIME_FORMAT)
        messages.append(f"{msg.id}) {date}:\n{msg.text}\n")
    await bot.send("List of all messages\n" + "\n".join(messages))


CHAT_SEP = "/"


@bot.command("chats")
async def accessible_chats(bot: Bot, text: str) -> None:
    criteria = model_attr(Chat.id).in_(bot.msg.author.accessible_chats)
    chats = await bot.db.read_all(Chat, criteria)
    names = [
        f"{i+1} {chat.represent_name(CHAT_SEP)}" for i, chat in enumerate(chats)
    ]
    await bot.send("List of accessible chats\n" + "\n".join(names))


@bot.command("start", "help")
async def greet(bot: Bot, text: str) -> None:
    await bot.send(
        "Hi, I'm RestlessFunnelBot!\n"
        "I listen to others, and then I retell everything to you 🤗\n"
    )


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
            await bot.handle_message(db, in_msg, msg)
