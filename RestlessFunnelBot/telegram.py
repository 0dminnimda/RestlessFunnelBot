import logging
from asyncio import ALL_COMPLETED, gather, wait

from aiogram import Bot, Dispatcher
from aiogram import types as aiots

from . import models, secrets
from .db import make_db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=secrets.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot=bot)


def message_to_model(msg: aiots.Message) -> models.Message:
    return models.Message(
        text=msg.text, timestamp=msg.date, platform=models.Platform.TELEGRAM
    )


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: aiots.Message):
    print("hi", message.text)
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler(commands=["list"])
async def send_list(message: aiots.Message):
    async with make_db() as db:
        messages = []
        for msg in await db.read_messages():
            messages.append("-" * 50 + f"\n{msg.id}: {msg.text}")
        await message.answer("\n\n".join(messages))


@dp.message_handler()
async def echo(msg: aiots.Message):
    async with make_db() as db:
        print("mes", msg.text, msg.chat.type)
        if msg.chat.type == aiots.ChatType.GROUP:
            await db.create_message(message_to_model(msg))
        await msg.answer(msg.text)


async def run():
    try:
        await dp.start_polling()
    finally:
        await bot.close()
    # executor.start_polling(dp, skip_updates=True)
