import logging
from typing import Any, Dict, Optional

import discord
from discord.abc import GuildChannel as TargetPublicChat
from discord.channel import DMChannel as TargetPrivateChat
from discord.enums import ChannelType as TargetChatType
from discord.message import Message as TargetMessage
from discord.user import BaseUser as TargetUser
from discord.user import _UserTag as TargetUserTag
from discord.utils import MISSING

from . import bot_secrets
from .bot import bot as main_bot
from .common import handle_message
from .mappers import model_mapper
from .models import DISCORD as PLATFORM
from .models import Chat, Message, User


@model_mapper(TargetMessage, Message)
def message_to_model(msg: TargetMessage) -> Dict[str, Any]:
    return dict(
        target_id=msg.id,
        text=msg.content,
        timestamp=msg.created_at,
    )


@model_mapper(TargetUserTag, User)
def user_to_model(user: TargetUser) -> Dict[str, Any]:
    return dict(
        target_id=user.id,
    )


@model_mapper(TargetPublicChat, Chat)
def public_chat_to_model(chat: TargetPublicChat) -> Dict[str, Any]:
    names = [chat.guild.name, chat.name]
    if chat.category:
        names.insert(1, chat.category.name)
    return dict(
        target_id=chat.id,
        name=Chat.generate_name(*names),
    )


@model_mapper(TargetPrivateChat, Chat)
def private_chat_to_model(chat: TargetPrivateChat) -> Dict[str, Any]:
    return dict(
        target_id=chat.id,
        name=Chat.generate_name(chat.me.display_name),
    )


@main_bot.send_function(TargetMessage)
async def send(msg: TargetMessage, text: str, mention: bool, raw: bool) -> None:
    if raw:
        if "\n" in text:
            text = f"```{text}```"
        else:
            text = f"`{text}`"

    if mention:
        await msg.channel.send(text, reference=msg)
    else:
        await msg.channel.send(text)


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready() -> None:
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(in_msg: TargetMessage) -> None:
    if in_msg.author == client.user:
        return

    if in_msg.channel.type not in {TargetChatType.text, TargetChatType.private}:
        return

    is_private = in_msg.channel.type == TargetChatType.private
    await handle_message(PLATFORM, in_msg, in_msg.channel, in_msg.author, is_private)


async def run(reconnect: bool = True) -> None:
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
        await client.start(bot_secrets.DISCORD_API_TOKEN, reconnect=reconnect)


def run_sync() -> None:
    client.run(bot_secrets.DISCORD_API_TOKEN)
