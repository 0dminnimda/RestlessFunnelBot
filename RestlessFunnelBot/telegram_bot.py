import logging
from asyncio import gather
from typing import Any, Dict

from aiogram import Bot, Dispatcher
from aiogram import types as aiots

from . import secrets
from .db import make_db, model_mapper
from .models import TELEGRAM


@model_mapper(aiots.Message)
def message_to_model(msg: aiots.Message) -> Dict[str, Any]:
    return dict(text=msg.text, timestamp=msg.date)


@model_mapper(aiots.User)
def user_to_model(user: aiots.User) -> Dict[str, Any]:
    return dict(id=user.id)


@model_mapper(aiots.Chat)
def chat_to_model(chat: aiots.Chat) -> Dict[str, Any]:
    return dict(id=chat.id)


logging.basicConfig(level=logging.INFO)

bot = Bot(token=secrets.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot=bot)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(in_msg: aiots.Message):
    await in_msg.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler(commands=["list"])
async def list_command(in_msg: aiots.Message):
    async with make_db(TELEGRAM) as db:
        messages = []
        for msg in await db.read_messages():
            messages.append("-" * 50 + f"\n{msg.id}: {msg.text}")

        await in_msg.reply("\n\n".join(messages))


@dp.message_handler(commands=["chats"])
async def chats_command(in_msg: aiots.Message):
    async with make_db(TELEGRAM) as db:
        user = await db.get_user(in_msg.from_id)
        tasks = [bot.get_chat(chat_id) for chat_id in user.accessible_chats]
        chats = [f"{i+1} {chat.title}" for i, chat in enumerate(await gather(*tasks))]
        await in_msg.reply("\n".join(chats))


@dp.message_handler()
async def collect_messages(in_msg: aiots.Message):
    async with make_db(TELEGRAM) as db:
        print("mes", in_msg.text, in_msg.chat.type)
        if in_msg.chat.type == aiots.ChatType.GROUP:
            db.create_message(in_msg)

            user = await db.get_user(in_msg.from_id)
            user.add_chat(in_msg.chat.id)

        await in_msg.answer(in_msg.text)


async def run():
    try:
        await dp.start_polling()
    finally:
        await bot.close()
    # executor.start_polling(dp, skip_updates=True)
