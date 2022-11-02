from time import time
from typing import Any, Dict, Optional, Tuple, cast, Set, List

from .bot import DEFAULT_COMMAND, Bot, bot
from .database import DataBase, make_db
from .mappers import map_model
from .models import Chat, Message, Platform, User, model_attr, to_moscow_tz
from .ttldict import TTLDict


@bot.command("start", "help")
async def greet(bot: Bot, text: str) -> None:
    await bot.send(
        "Hi, I'm RestlessFunnelBot!\n"
        "I listen to others, and then I retell everything to you 🤗\n"
    )


@bot.command(DEFAULT_COMMAND)
async def default_response(bot: Bot, text: str) -> None:
    await bot.send("Sorry, I don't understand you, can you repeat again, please?")


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
    names = [f"{i+1} {chat.represent_name(CHAT_SEP)}" for i, chat in enumerate(chats)]
    await bot.send("List of accessible chats\n" + "\n".join(names))


AUTH_TTL = 60
auth_ids: TTLDict[int, bool] = TTLDict(AUTH_TTL, 32)
auth_keys: TTLDict[str, int] = TTLDict(AUTH_TTL, 32)


def expire_auth():
    for id in auth_keys.expire():
        auth_ids.pop(id)
    auth_ids.expire()


def set_auth_key(id: int, key: str) -> str:
    auth_ids[id] = True
    auth_keys[key] = id
    return key


@bot.command("link")
async def link(bot: Bot, text: str) -> None:
    text = text.strip(" ")
    user_id = cast(int, bot.msg.author.id)

    if text:
        other_user_id = auth_keys.get(text)
        if other_user_id is None:
            await bot.send("This secret code is outdated or invalid :(")
        elif other_user_id == user_id:
            await bot.send("You can't link to the same account")
        else:
            await bot.send("Successfully linked!")
            await bot.send(f"DEBUG: with {other_user_id}")
            auth_ids.pop(other_user_id)
            auth_keys.pop(text)
    else:
        if auth_ids.get(user_id):
            await bot.send("You have already generated a secret code")
        else:
            key = set_auth_key(user_id, f"ur-mom-{user_id}")
            await bot.send(
                "With this command you link your account to another account\n"
                "\n"
                f"I created a temporary a secret code for you: {key}\n"
                f"Hurry, it will last only for {AUTH_TTL} seconds\n"
                "\n"
                "To use it log into another account and send this message:"
            )
            await bot.send(f"/link {key}", raw=True)


async def make_message(
    db: DataBase, in_msg: Any, chat: Any, author: Any, is_private: bool
) -> Message:
    fields = map_model(in_msg)

    chat = fields["chat"] = await db.read_or_create(Chat, **map_model(chat))
    author = fields["author"] = await db.read_or_create(User, **map_model(author))
    await db.flush()

    fields["chat_id"] = chat.id
    fields["author_id"] = author.id

    msg = db.create_no_add(Message, **fields)
    if not is_private:
        author.add_chat(chat)
        db.add(msg)
    return msg


async def handle_message(
    platform: Platform, in_msg: Any, chat: Any, author: Any, is_private: bool
) -> None:
    expire_auth()
    async with make_db(platform) as db:
        msg = await make_message(db, in_msg, chat, author, is_private)
        if is_private:
            await bot.handle_message(db, in_msg, msg)
    # print(auth_ids, auth_keys)
