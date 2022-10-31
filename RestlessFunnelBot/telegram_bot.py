import logging
from asyncio import gather
from typing import Any, Dict

from aiogram import Bot, Dispatcher
# from aiogram import types as aiots
from aiogram.types import Chat as TargetChat
from aiogram.types import ChatType as TargetChatType
from aiogram.types import Message as TargetMessage
from aiogram.types import User as TargetUser

from . import secrets
from .common import handle_new_message
from .database import make_db
from .mappers import map_model, model_mapper
from .models import TELEGRAM as PLATFORM
from .models import Chat, Message, Platform, User


@model_mapper(TargetMessage, Message)
def message_to_model(msg: TargetMessage) -> Dict[str, Any]:
    author = msg.from_user
    chat = msg.chat
    return dict(
        text=msg.text,
        timestamp=msg.date,
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
    return dict(id=chat.id, name=Chat.generate_name(chat.title))


logging.basicConfig(level=logging.INFO)

bot = Bot(token=secrets.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot=bot)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(in_msg: TargetMessage):
    await in_msg.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler()
async def collect_messages(in_msg: TargetMessage):
    # print("mes", in_msg.text, in_msg.chat.type)

    if in_msg.chat.type != TargetChatType.GROUP:
        return

    async with make_db(PLATFORM) as db:
        result = await handle_new_message(db, in_msg)

    if result:
        await in_msg.reply(result)

    # await in_msg.answer(in_msg.text)


async def run():
    try:
        await dp.start_polling()
    finally:
        await bot.close()

    # executor.start_polling(dp, skip_updates=True)
