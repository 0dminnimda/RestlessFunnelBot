from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, List, Optional, Type, TypeVar

from sqlalchemy import func as sql_func
from sqlalchemy.engine import Result, ScalarResult
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnClause
from sqlalchemy.orm import load_only
from sqlalchemy.sql.roles import ExpressionElementRole
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from . import options
from .models import Platform

DATABASE_URL = f"sqlite+aiosqlite:///{Path(__file__).parent}/sqlite.db"

engine = create_async_engine(
    DATABASE_URL, future=True, connect_args={"check_same_thread": False}
)


async def db_startup() -> None:
    async with engine.begin() as conn:
        if options.DEV_MODE:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def db_shutdown() -> None:
    if options.DEV_MODE:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@asynccontextmanager
async def db_tables() -> AsyncGenerator[None, None]:
    await db_startup()
    try:
        yield
    except Exception:
        await db_shutdown()


T = TypeVar("T", bound=Any)


class DataBase(AsyncSession):
    def __init__(self, *args, platform: Platform, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.platform = platform

    async def fetch(self, selection: Select) -> ScalarResult:
        result: Result = await self.execute(selection)
        return result.scalars()

    async def count(self, model: Type[T], *args, **kwargs: Any) -> int:
        selection = select(model).filter(*args).filter_by(**kwargs).options(load_only())
        return len((await self.fetch(selection)).all())

    async def read_all(self, model: Type[T], *args, **kwargs: Any) -> List[T]:
        selection = select(model).filter(*args).filter_by(**kwargs)
        return (await self.fetch(selection)).all()

    async def read_one(self, model: Type[T], *args, **kwargs: Any) -> T:
        selection = select(model).filter(*args).filter_by(**kwargs)
        return (await self.fetch(selection)).one()

    async def read_one_or_none(
        self, model: Type[T], *args, **kwargs: Any
    ) -> Optional[T]:
        selection = select(model).filter(*args).filter_by(**kwargs)
        return (await self.fetch(selection)).one_or_none()

    def create_no_add(self, model: Type[T], **kwargs: Any) -> T:
        kwargs["platform"] = self.platform
        return model(**kwargs)

    def create(self, model: Type[T], **kwargs: Any) -> T:
        instance = self.create_no_add(model, **kwargs)
        self.add(instance)
        return instance

    async def read_or_create(self, model: Type[T], **kwargs: Any) -> T:
        kwargs["platform"] = self.platform
        instance = await self.read_one_or_none(model, **kwargs)
        if instance is not None:
            return instance
        return self.create(model, **kwargs)


def make_session(platform: Platform) -> DataBase:
    return DataBase(bind=engine, expire_on_commit=False, platform=platform)


async def get_db(
    platform: Platform, commit: bool = True
) -> AsyncGenerator[DataBase, None]:
    async with make_session(platform) as session:
        async with session.begin():
            try:
                yield session
                if commit:
                    await session.commit()
            except Exception:
                await session.rollback()
                raise


make_db = asynccontextmanager(get_db)
