import logging
from typing import Any, Dict

from aiogram import Bot, Dispatcher, executor, utils
from aiogram.types import Chat as TargetChat
from aiogram.types import ChatType as TargetChatType
from aiogram.types import Message as TargetMessage
from aiogram.types import ParseMode
from aiogram.types import User as TargetUser

from . import bot_secrets
from .__metadata__ import BOT_NAME
from .bot import bot as main_bot
from .common import handle_message
from .mappers import model_mapper
from .models import TELEGRAM as PLATFORM
from .models import Chat, Message, User, from_moscow_tz


@model_mapper(TargetMessage, Message)
def message_to_model(msg: TargetMessage) -> Dict[str, Any]:
    return dict(
        target_id=msg.message_id,
        text=msg.text,
        timestamp=from_moscow_tz(msg.date),
    )


@model_mapper(TargetUser, User)
def user_to_model(user: TargetUser) -> Dict[str, Any]:
    return dict(
        target_id=user.id,
    )


@model_mapper(TargetChat, Chat)
def chat_to_model(chat: TargetChat) -> Dict[str, Any]:
    return dict(
        target_id=chat.id,
        name=Chat.generate_name(chat.title or BOT_NAME),
    )


@main_bot.send_function(TargetMessage)
async def send(msg: TargetMessage, text: str, mention: bool, raw: bool) -> None:
    parse_mode = None
    if raw:
        parse_mode = ParseMode.MARKDOWN_V2
        text = utils.markdown.escape_md(text)
        if "\n" in text:
            text = f"```{text}```"
        else:
            text = f"`{text}`"

    if mention:
        await msg.reply(text, parse_mode=parse_mode)
    else:
        await msg.answer(text, parse_mode=parse_mode)


logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_secrets.TELEGRAM_API_TOKEN)
dp = Dispatcher(bot=bot)


@dp.message_handler()
async def on_message(in_msg: TargetMessage) -> None:
    is_private = in_msg.chat.type == TargetChatType.PRIVATE
    await handle_message(PLATFORM, in_msg, in_msg.chat, in_msg.from_user, is_private)


async def run() -> None:
    # try:
    await dp.start_polling()
    # finally:
    #     await dp.wait_closed()
    #     dp.stop_polling()
    #     await bot.close()


def run_sync() -> None:
    executor.start_polling(dp, skip_updates=False)

# XXX: try telethon or pyrogram for MTP
