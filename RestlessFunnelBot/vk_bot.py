from datetime import datetime
from typing import Any, Dict

from vkbottle.bot import Bot
from vkbottle.bot import Message as TargetMessage
from vkbottle_types.objects import MessagesConversation as TargetChat
from vkbottle_types.objects import MessagesConversationPeerType as TargetChatType
from vkbottle_types.objects import UsersUserFull as TargetUser

from . import secrets
from .common import handle_message
from .mappers import model_mapper
from .messenger import answer_function, reply_function
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
        id=user.id,
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
        id=chat.peer.id,
        name=Chat.generate_name(title),
    )


@reply_function(TargetMessage)
async def reply_to(msg: TargetMessage, text: str) -> None:
    await msg.reply(text)


@answer_function(TargetMessage)
async def answer_to(msg: TargetMessage, text: str) -> None:
    await msg.answer(text)


bot = Bot(token=secrets.VK_API_TOKEN)
GROUP_ID = -1
GROUP_NAME = "<unknown>"


async def on_ready() -> None:
    global GROUP_ID, GROUP_NAME
    group = (await bot.api.groups.get_by_id())[0]
    GROUP_ID = group.id
    GROUP_NAME = group.name


@bot.on.message()
async def on_message(in_msg: TargetMessage) -> None:
    (chat,) = (await bot.api.messages.get_conversations_by_id(in_msg.peer_id)).items
    (author,) = await bot.api.users.get(in_msg.from_id)

    # also works: is_private = in_msg.peer_id == in_msg.from_id
    is_private = chat.peer.type == TargetChatType.USER
    await handle_message(PLATFORM, in_msg, chat, author, is_private)


async def run() -> None:
    await on_ready()
    await bot.run_polling()


def run_sync() -> None:
    bot.loop_wrapper.on_startup.append(on_ready())
    bot.run_forever()
