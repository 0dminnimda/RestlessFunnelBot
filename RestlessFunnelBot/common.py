from typing import Any, Set, cast
import secrets
import string

from .__metadata__ import BOT_NAME
from .bot import DEFAULT_COMMAND, Bot, bot
from .database import DataBase, make_db
from .mappers import map_model
from .models import Chat, ConnectedUser, Message, Platform, User, col, to_moscow_tz
from .ttldict import TTLDict


@bot.command("start", "help")
async def greet(bot: Bot, text: str) -> None:
    await bot.send(
        f"Hi, I'm {BOT_NAME}!\n"
        "I listen to others, and then I retell everything to you 🤗\n"
    )
    await commands(bot, text)
    await bot.send(
        "If you want me to listen to some chat, "
        "add me there, give me required permissions "
        "and send one message there"
    )


@bot.command("commands")
async def commands(bot: Bot, text: str) -> None:
    await bot.send(
        "Here are my commands:\n"
        + "\n".join(
            "- /" + com for com in bot.commands.keys() if com != DEFAULT_COMMAND
        )
    )


@bot.command(DEFAULT_COMMAND)
async def default_response(bot: Bot, text: str) -> None:
    await bot.send(
        "Sorry, I don't understand you, can you repeat again, please?\n"
        "If you are lost check out /help command!"
    )


TIME_FORMAT = "%d %B %Y - %H:%M:%S (%Z)"


@bot.command("list")
async def all_messages(bot: Bot, text: str) -> None:
    messages = []
    criteria = col(Message.chat_id).in_(bot.msg.author.connection.chats)
    for i, msg in enumerate(await bot.db.read_all(Message, criteria)):
        date = to_moscow_tz(msg.timestamp).strftime(TIME_FORMAT)
        messages.append(f"{i+1}) {date}:\n{msg.text}\n")
    await bot.send("List of all messages\n" + "\n".join(messages))


CHAT_SEP = "/"


@bot.command("chats")
async def accessible_chats(bot: Bot, text: str) -> None:
    criteria = col(Chat.id).in_(bot.msg.author.connection.chats)
    chats = await bot.db.read_all(Chat, criteria)
    names = [f"{i+1} {chat.represent_name(CHAT_SEP)}" for i, chat in enumerate(chats)]
    await bot.send("List of accessible chats\n" + "\n".join(names))


AUTH_TTL = 60
EXPIRE_COUNT = 128
auth_ids: TTLDict[int, bool] = TTLDict(AUTH_TTL, EXPIRE_COUNT)
auth_keys: TTLDict[str, int] = TTLDict(AUTH_TTL, EXPIRE_COUNT)


def expire_auth():
    for id in auth_keys.expire():
        auth_ids.pop(id)
    auth_ids.expire()


def set_auth_key(id: int, key: str) -> str:
    auth_ids[id] = True
    auth_keys[key] = id
    return key


async def actually_link(bot: Bot, other_user_id: int) -> None:
    other = await bot.db.read_one(User, id=other_user_id)
    if other.connection_id == bot.msg.author.connection_id:
        return
    other_connection = await bot.db.read_one(ConnectedUser, id=other.connection_id)

    all_others = await bot.db.read_all(User, connection_id=other.connection_id)
    for user in all_others:
        user.connection_id = bot.msg.author.connection_id
        user.connection = bot.msg.author.connection

    bot.msg.author.connection.add_chats_from(other_connection)
    await bot.db.delete(other_connection)


KEY_ALPHABET = string.digits * 10 + string.ascii_letters * 7 + "!?$%^&.,_~@:;/\\=" * 4


def generate_auth_key(length: int = 42) -> str:
    # secrets.token_urlsafe()
    return "".join(secrets.choice(KEY_ALPHABET) for _ in range(length))


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
            del auth_ids[other_user_id]
            del auth_keys[text]
            await actually_link(bot, other_user_id)
            await bot.send("Successfully linked!")
    else:
        if auth_ids.get(user_id):
            await bot.send("You have already generated a secret code")
        else:
            key = set_auth_key(user_id, generate_auth_key())
            await bot.send(
                "With this command you link your account to another account\n"
                "\n"
                f"I created a temporary a secret code for you\n"
                f"Hurry up, it will last only for {AUTH_TTL} seconds!\n"
                "\n"
                "To use it log into another account and send this message:"
            )
            await bot.send(f"/link {key}", raw=True)


async def actually_unlink(bot: Bot, unlink_ids: Set[int]) -> None:
    all_linked = await bot.db.read_all(User, connection_id=bot.msg.author.connection_id)

    to_unlink = []
    left_linked = []
    for user in all_linked:
        if user.id in unlink_ids:
            to_unlink.append(user)
        else:
            left_linked.append(user)

    unlink_connection = bot.msg.author.connection
    left_connection = bot.db.create(ConnectedUser)
    await bot.db.flush()

    unlink_connection.chats = sorted(set().union(*(user.chats for user in to_unlink)))
    left_connection.chats = sorted(set().union(*(user.chats for user in left_linked)))

    assert left_connection.id is not None
    for user in left_linked:
        user.connection_id = left_connection.id
        user.connection = left_connection

    if len(to_unlink) == 0:
        await bot.db.delete(unlink_connection)
    if len(left_linked) == 0:
        await bot.db.delete(left_connection)


@bot.command("unlink")
async def unlink(bot: Bot, text: str) -> None:
    text = text.strip(" ")

    if text:
        if text == "all":
            linked = await bot.db.read_all(
                User, connection_id=bot.msg.author.connection_id
            )
            await actually_unlink(
                bot,
                {cast(int, user.id) for user in linked}
                - {cast(int, bot.msg.author.id)},
            )
            await bot.send(f"Successfully unlinked all")
        else:
            await bot.send(f"I could not find unlink option '{text}'")
    else:
        await bot.send("You need to specify which accounts are going to be unlinked")
        await bot.send("/unlink options", raw=True)
        await bot.send("Current options are:\n" "- all")


async def read_or_create_user(db: DataBase, **fields: Any) -> User:
    user = await db.read_one_or_none(User, **fields)
    if user is not None:
        user.connection = await db.read_one(ConnectedUser, id=user.connection_id)
        return user

    fields["connection"] = connection = db.create(ConnectedUser)
    await db.flush()

    fields["connection_id"] = connection.id
    return db.create(User, **fields)


async def make_message(
    db: DataBase, in_msg: Any, chat: Any, author: Any, is_private: bool
) -> Message:
    fields = map_model(in_msg)

    chat = fields["chat"] = await db.read_or_create(Chat, **map_model(chat))
    author = fields["author"] = await read_or_create_user(db, **map_model(author))
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
