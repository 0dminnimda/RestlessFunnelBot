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
from .database import make_db
from .mappers import map_model, model_mapper
from .models import TELEGRAM as PLATFORM


@model_mapper(TargetMessage)
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


@model_mapper(TargetUser)
def user_to_model(user: TargetUser) -> Dict[str, Any]:
    return dict(id=user.id)


@model_mapper(TargetChat)
def chat_to_model(chat: TargetChat) -> Dict[str, Any]:
    return dict(id=chat.id)


logging.basicConfig(level=logging.INFO)

bot = Bot(token=secrets.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot=bot)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(in_msg: TargetMessage):
    await in_msg.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler(commands=["list"])
async def list_command(in_msg: TargetMessage):
    async with make_db(PLATFORM) as db:
        messages = []
        for msg in await db.read_messages():
            messages.append("-" * 50 + f"\n{msg.id}: {msg.text}")

        await in_msg.reply("List of all messages\n" + "\n\n".join(messages))


@dp.message_handler(commands=["chats"])
async def chats_command(in_msg: TargetMessage):
    async with make_db(PLATFORM) as db:
        user = await db.get_user(in_msg.from_user)
        tasks = [bot.get_chat(chat_id) for chat_id in user.accessible_chats]
        chats = [f"{i+1} {chat.title}" for i, chat in enumerate(await gather(*tasks))]
        await in_msg.reply("List of accessible chats\n" + "\n".join(chats))


@dp.message_handler()
async def collect_messages(in_msg: TargetMessage):
    async with make_db(PLATFORM) as db:
        print("mes", in_msg.text, in_msg.chat.type)
        if in_msg.chat.type == TargetChatType.GROUP:
            db.create_message(in_msg)

            user = await db.get_user(in_msg.from_user)
            user.add_chat(in_msg.chat.id)

        await in_msg.answer(in_msg.text)


async def run():
    try:
        await dp.start_polling()
    finally:
        await bot.close()

    # executor.start_polling(dp, skip_updates=True)
