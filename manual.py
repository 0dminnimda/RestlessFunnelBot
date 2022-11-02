# Temporary manual test

from asyncio import gather
from asyncio import run as run_async

from RestlessFunnelBot import discord_bot, telegram_bot, vk_bot
from RestlessFunnelBot.database import db_tables


async def main() -> None:
    async with db_tables():
        await gather(
            vk_bot.run(),
            discord_bot.run(),
            telegram_bot.run(),
        )


run_async(main())
