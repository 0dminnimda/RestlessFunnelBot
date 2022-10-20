import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.handler import SkipHandler
from aiogram.types import ChatType

from . import secrets
from .db import save_message, Message, Platform

logging.basicConfig(level=logging.INFO)

bot = Bot(token=secrets.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot=bot)


# print("ggggggggggggggg")


def message_to_model(msg: types.Message) -> Message:
    return Message(text=msg.text, timestamp=msg.date, platform=Platform.TELEGRAM)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    print("hi", message.text)
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dp.message_handler()
async def echo(msg: types.Message):
    print("mes", msg.text, msg.chat.type)
    if msg.chat.type == ChatType.GROUP:
        save_message(message_to_model(msg))
    await msg.answer(msg.text)


# async def main():
#     bot = Bot(token=secrets.TELEGRAM_API_TOKEN)
#     try:
#         disp = Dispatcher(bot=bot)
#         disp.register_message_handler(start_handler, commands={"start", "restart"})
#         await disp.start_polling()
#     finally:
#         await bot.close()


def run():
    # asyncio.run(main())
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    run()
