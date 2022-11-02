from time import time
from typing import Any, Dict, Optional, Tuple, cast, Set, List

from .bot import DEFAULT_COMMAND, Bot, bot
from .database import DataBase, make_db
from .mappers import map_model
from .models import Chat, Message, Platform, User, model_attr, to_moscow_tz


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


auth_keys: Dict[int, str] = {}
auth_key_info: Dict[str, Tuple[float, int]] = {}
KEY_LIFE_TIME = 60


def delete_outdated_auth_keys(max_number_of_elements: int = 256):
    """
    This function relies on the fact that dict is ordered.
    More often calls -> faster execution time.
    Complexity is ~O(n*sigmiod(x)) where n is number of keys
    and x is how much time passed from the last update.
    """

    keys = set()

    current_time = time()
    for key, (timestamp, id) in auth_key_info.items():
        if current_time - timestamp <= KEY_LIFE_TIME:
            break

        keys.add(key)
        key_ = auth_keys.pop(id, None)
        if key_ is not None:
            keys.add(key_)

        max_number_of_elements -= 1
        if max_number_of_elements <= 0:
            break

    for key in keys:
        auth_key_info.pop(key, None)


def set_auth_key(id: int, key: str) -> str:
    auth_keys[id] = key
    auth_key_info[key] = (time(), id)
    return key


@bot.command("link")
async def link(bot: Bot, text: str) -> None:
    text = text.strip(" ")
    user_id = cast(int, bot.msg.author.id)
    delete_outdated_auth_keys()

    if text:
        other_user_id = auth_key_info.get(text)
        if other_user_id is None:
            await bot.send("This secret code is invalid :(")
            # await bot.send("No such secret code found :(")
        else:
            await bot.send("Successfully linked!")
            await bot.send(f"DEBUG: with {other_user_id[1]}")
            auth_keys.pop(user_id, None)
            auth_key_info.pop(text, None)
    else:
        key = auth_keys.get(user_id)
        if key is None:
            key = set_auth_key(user_id, f"ur-mom-{user_id}")
            await bot.send(
                "With this command you link your account to another account\n"
                "\n"
                f"I created a temporary a secret code for you: {key}\n"
                f"Hurry, it will last only for {KEY_LIFE_TIME} seconds\n"
                "\n"
                "To use it log into another account and send this message:"
            )
            await bot.send(f"`/link {key}`")
        else:
            await bot.send("You already have generated a secret code")
            await bot.send(f"`/link {key}`")


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
    async with make_db(platform) as db:
        msg = await make_message(db, in_msg, chat, author, is_private)
        if is_private:
            await bot.handle_message(db, in_msg, msg)
