# Temporary manual test

from asyncio import run as run_async

from RestlessFunnelBot import telegram_bot
from RestlessFunnelBot.db import db_tables


async def main():
    async with db_tables():
        await telegram_bot.run()


run_async(main())
