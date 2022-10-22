# Temporary manual test

from asyncio import run as run_async

from RestlessFunnelBot.db import db_tables
from RestlessFunnelBot.telegram import run


async def main():
    async with db_tables():
        await run()


run_async(main())
