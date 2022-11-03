"""
This file allows you to run the app programmatically,
and also enables debugging if this file is run as the main
"""

import asyncio

from RestlessFunnelBot import discord_bot, options, telegram_bot, vk_bot
from RestlessFunnelBot.database import db_tables


async def run_all() -> None:
    async with db_tables():
        await asyncio.gather(
            vk_bot.run(),
            discord_bot.run(),
            telegram_bot.run(),
        )


def run_all_sync() -> None:
    asyncio.run(run_all())


run = run_all_sync


if __name__ in ("__mp_main__", "__main__"):
    # if this file is launched directly, this is a sign that it is a dev
    options.DEV_MODE = True

if __name__ == "__main__":
    run()