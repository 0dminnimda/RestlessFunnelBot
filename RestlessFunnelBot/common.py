import re
from typing import Any, Dict, Optional, Tuple, Callable, Awaitable

from .database import DataBase, make_db
from .mappers import map_model
from .messenger import Messenger
from .models import Chat, Message, Platform, User, model_attr, to_moscow_tz


# COMMAND_PATTERN = r"(?:/(?P<command>\w+) )?\s*(?P<text>.+)"
# COMMAND_PATTERN = r"(?:/(\w+)\s*)?(.+)"
COMMAND_PATTERN = r"(?:/(\S+))? *(.*)"
COMMAND_REGEXP = re.compile(COMMAND_PATTERN)


CommandHandler = Callable[["Bot", str], Awaitable[None]]


class Bot(Messenger):
    db: DataBase
    msg: Message

    commands: Dict[str, CommandHandler] = {}

    def command(self, *names: str) -> Callable[[CommandHandler], CommandHandler]:
        def inner(f: CommandHandler) -> CommandHandler:
            for name in names:
                self.commands[name] = f
            return f
        return inner

    async def reply(self, db: DataBase, in_msg: Any, msg: Message) -> None:
        self.target_message = in_msg
        self.db = db
        self.msg = msg

        match = COMMAND_REGEXP.match(msg.text)
        if match is None:
            return
        command, text = match.groups()

        func = self.commands.get(command)
        if func is not None:
            await func(self, text)


bot = Bot()


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
            await bot.reply(db, in_msg, msg)
