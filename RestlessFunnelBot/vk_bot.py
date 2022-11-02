from datetime import datetime
from typing import Any, Dict, cast

from vkbottle.bot import Bot
from vkbottle.bot import Message as TargetMessage
from vkbottle_types.objects import MessagesConversation as TargetChat
from vkbottle_types.objects import MessagesConversationPeerType as TargetChatType
from vkbottle_types.objects import UsersUserFull as TargetUser

from . import secrets
from .bot import bot as main_bot
from .common import handle_message
from .mappers import model_mapper
from .models import VK as PLATFORM
from .models import Chat, Message, User


@model_mapper(TargetMessage, Message)
def message_to_model(msg: TargetMessage) -> Dict[str, Any]:
    # msg.message_id
    return dict(
        text=msg.text,
        timestamp=datetime.utcfromtimestamp(msg.date),
    )


@model_mapper(TargetUser, User)
def user_to_model(user: TargetUser) -> Dict[str, Any]:
    return dict(
        target_id=user.id,
    )


@model_mapper(TargetChat, Chat)
def chat_to_model(chat: TargetChat) -> Dict[str, Any]:
    if chat.peer.type == TargetChatType.USER:
        title = GROUP_NAME
    elif chat.chat_settings is not None:
        title = chat.chat_settings.title
    else:
        title = f"<Chat ({chat.peer.id}) name not found>"

    return dict(
        target_id=chat.peer.id,
        name=Chat.generate_name(title),
    )


@main_bot.send_function(TargetMessage)
async def send(msg: TargetMessage, text: str, mention: bool) -> None:
    if mention:
        await msg.reply(text)
    else:
        await msg.answer(text)


bot = Bot(token=secrets.VK_API_TOKEN)
GROUP_ID: int = -1
GROUP_NAME: str = "<unknown>"


async def on_ready() -> None:
    global GROUP_ID, GROUP_NAME
    group = (await bot.api.groups.get_by_id())[0]
    GROUP_ID = group.id
    if group.name is not None:
        GROUP_NAME = group.name


@bot.on.message()
async def on_message(in_msg: TargetMessage) -> None:
    peer_ids = cast(list, in_msg.peer_id)
    (chat,) = (await bot.api.messages.get_conversations_by_id(peer_ids)).items
    user_ids = cast(list, in_msg.from_id)
    (author,) = await bot.api.users.get(user_ids)

    # also works: is_private = in_msg.peer_id == in_msg.from_id
    is_private = chat.peer.type == TargetChatType.USER
    await handle_message(PLATFORM, in_msg, chat, author, is_private)


async def run() -> None:
    await on_ready()
    await bot.run_polling()


def run_sync() -> None:
    bot.loop_wrapper.on_startup.append(on_ready())
    bot.run_forever()
