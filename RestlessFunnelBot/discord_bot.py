import logging
from typing import Any, Dict, Optional

import discord
from discord.abc import GuildChannel as TargetChat
from discord.enums import ChannelType as TargetChatType
from discord.member import Member as TargetUser
from discord.message import Message as TargetMessage
from discord.utils import MISSING

from . import secrets
from .common import handle_new_message
from .database import make_db
from .mappers import model_mapper
from .models import DISCORD as PLATFORM
from .models import Chat, Message, User


@model_mapper(TargetMessage, Message)
def message_to_model(msg: TargetMessage) -> Dict[str, Any]:
    author = msg.author
    chat = msg.channel
    return dict(
        text=msg.content,
        timestamp=msg.created_at,
        author=author,
        author_id=author.id,
        chat=chat,
        chat_id=chat.id,
    )


@model_mapper(TargetUser, User)
def user_to_model(user: TargetUser) -> Dict[str, Any]:
    return dict(id=user.id)


@model_mapper(TargetChat, Chat)
def chat_to_model(chat: TargetChat) -> Dict[str, Any]:
    names = [chat.guild.name, chat.name]
    if chat.category:
        names.insert(1, chat.category.name)
    return dict(id=chat.id, name=Chat.generate_name(*names))


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(in_msg):
    if in_msg.author == client.user:
        return

    if in_msg.channel.type != TargetChatType.text:
        return

    async with make_db(PLATFORM) as db:
        result = await handle_new_message(db, in_msg)

    if result:
        await in_msg.channel.send(result, reference=in_msg)

    # await in_msg.channel.send(in_msg.content)


async def run(reconnect: bool = True):
    log_handler: Optional[logging.Handler] = MISSING
    log_formatter: logging.Formatter = MISSING
    log_level: int = MISSING
    root_logger: bool = False

    if log_handler is not None:
        discord.utils.setup_logging(
            handler=log_handler,
            formatter=log_formatter,
            level=log_level,
            root=root_logger,
        )

    async with client:
        await client.start(secrets.DISCORD_API_TOKEN, reconnect=reconnect)


def run_sync():
    client.run(secrets.DISCORD_API_TOKEN)
