# Temporary manual test

from asyncio import run as run_async

from RestlessFunnelBot import discord_bot, telegram_bot
from RestlessFunnelBot.database import db_tables


async def main():
    async with db_tables():
        # await telegram_bot.run()
        await discord_bot.run()


run_async(main())
