# Temporary manual test

from asyncio import ensure_future, gather, get_event_loop
from asyncio import run as run_async
from multiprocessing import Process

from RestlessFunnelBot import discord_bot, telegram_bot
from RestlessFunnelBot.database import db_shutdown, db_startup, db_tables


async def run_discord_bot():
    async with db_tables():
        await discord_bot.run()


async def run_telegram_bot():
    async with db_tables():
        await telegram_bot.run()


async def amain():
    async with db_tables():
        await gather(
            discord_bot.run(),
            telegram_bot.run(),
        )


def main():
    run_async(db_startup())

    try:
        p1 = Process(name="p1", target=run_async, args=(discord_bot.run(),))
        p2 = Process(name="p2", target=run_async, args=(telegram_bot.run(),))
        p1.start()
        p2.start()
    except Exception:
        run_async(db_shutdown())


run_async(amain())

# loop = get_event_loop()
# ensure_future(run_discord_bot())
# ensure_future(run_telegram_bot())
# loop.run_forever()
