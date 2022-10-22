from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, List

from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import Select
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import Message


class CRUD(AsyncSession):
    async def _fetch_all(self, selection: Select) -> List[Any]:
        result: Result = await self.execute(selection)
        return result.scalars().all()

    async def create_message(self, msg: Message) -> Message:
        print(msg)
        self.add(msg)
        return msg

    async def read_messages(self) -> List[Message]:
        selection = select(Message)
        return await self._fetch_all(selection)


def make_session() -> CRUD:
    return CRUD(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[CRUD, None]:
    async with make_session() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


make_db = asynccontextmanager(get_db)

DATABASE_URL = f"sqlite+aiosqlite:///{Path(__file__).parent}/sqlite.db"

engine = create_async_engine(
    DATABASE_URL, future=True, connect_args={"check_same_thread": False}
)


async def db_startup() -> None:
    async with engine.begin() as conn:
        # if options.DEV_MODE:
        #     await conn.run_sync(SQLModel.metadata.drop_all)  # type: ignore
        await conn.run_sync(SQLModel.metadata.drop_all)  # type: ignore
        await conn.run_sync(SQLModel.metadata.create_all)  # type: ignore


async def db_shutdown() -> None:
    # if options.DEV_MODE:
    #     async with engine.begin() as conn:
    #         await conn.run_sync(SQLModel.metadata.drop_all)  # type: ignore

    await engine.dispose()


@asynccontextmanager
async def db_tables() -> AsyncGenerator[None, None]:
    await db_startup()
    try:
        yield
    except Exception:
        await db_shutdown()
