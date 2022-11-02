import logging
from typing import Any, Dict

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Chat as TargetChat
from aiogram.types import ChatType as TargetChatType
from aiogram.types import Message as TargetMessage
from aiogram.types import User as TargetUser

from . import secrets
from .common import handle_message, from_moscow_tz
from .mappers import model_mapper
from .messenger import answer_function, reply_function
from .models import TELEGRAM as PLATFORM
from .models import Chat, Message, User


@model_mapper(TargetMessage, Message)
def message_to_model(msg: TargetMessage) -> Dict[str, Any]:
    return dict(
        text=msg.text,
        timestamp=from_moscow_tz(msg.date),
    )


@model_mapper(TargetUser, User)
def user_to_model(user: TargetUser) -> Dict[str, Any]:
    return dict(
        id=user.id,
    )


@model_mapper(TargetChat, Chat)
def chat_to_model(chat: TargetChat) -> Dict[str, Any]:
    return dict(
        id=chat.id,
        name=Chat.generate_name(chat.title or "RestlessFunnelBot"),
    )


@reply_function(TargetMessage)
async def reply_to(msg: TargetMessage, text: str) -> None:
    await msg.reply(text)


@answer_function(TargetMessage)
async def answer_to(msg: TargetMessage, text: str) -> None:
    await msg.answer(text)


logging.basicConfig(level=logging.INFO)

bot = Bot(token=secrets.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot=bot)


@dp.message_handler()
async def on_message(in_msg: TargetMessage) -> None:
    is_private = in_msg.chat.type == TargetChatType.PRIVATE
    await handle_message(PLATFORM, in_msg, in_msg.chat, in_msg.from_user, is_private)


async def run() -> None:
    try:
        await dp.start_polling()
    finally:
        await bot.close()


def run_sync() -> None:
    executor.start_polling(dp, skip_updates=False)
