from contextlib import asynccontextmanager
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from sqlalchemy.engine import Result, ScalarResult
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import Select
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import Message, Platform, User

DATABASE_URL = f"sqlite+aiosqlite:///{Path(__file__).parent}/sqlite.db"

engine = create_async_engine(
    DATABASE_URL, future=True, connect_args={"check_same_thread": False}
)


async def db_startup() -> None:
    async with engine.begin() as conn:
        # if options.DEV_MODE:
        #     await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def db_shutdown() -> None:
    # if options.DEV_MODE:
    #     async with engine.begin() as conn:
    #         await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@asynccontextmanager
async def db_tables() -> AsyncGenerator[None, None]:
    await db_startup()
    try:
        yield
    except Exception:
        await db_shutdown()


T = TypeVar("T", bound=Any)
ModelMapper = Callable[[T], Dict[str, Any]]
MapToModel = Dict[Type[T], ModelMapper]


_model_mappers: MapToModel = {}


def model_mapper(type_: Type[T]) -> Callable[[ModelMapper], ModelMapper]:
    def inner(f: ModelMapper) -> ModelMapper:
        _model_mappers[type_] = f
        return f

    return inner


class DataBase(AsyncSession):
    def __init__(self, *args, platform: Platform, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.platform = platform

    async def fetch(self, selection: Select) -> ScalarResult:
        result: Result = await self.execute(selection)
        return result.scalars()

    def create_raw(self, model: Type[T], *args: Any, **kwargs: Any) -> T:
        kwargs["platform"] = self.platform
        instance = model(*args, **kwargs)
        self.add(instance)
        return instance

    def create(self, model: Type[T], obj: Any) -> T:
        return self.create_raw(model, **_model_mappers[type(obj)](obj))

    # Message
    def create_message(self, obj: Any) -> Message:
        return self.create(Message, obj)

    async def read_messages(self) -> List[Message]:
        selection = select(Message)
        return (await self.fetch(selection)).all()

    # User
    def create_user(self, obj: Any) -> User:
        return self.create(User, obj)

    async def read_user(self, id: int) -> Optional[User]:
        selection = select(User).filter(User.id == id)
        return (await self.fetch(selection)).one_or_none()

    async def get_user(self, id: int) -> User:
        user = await self.read_user(id)
        if user is not None:
            return user
        return self.create_raw(User, id=id)

    # # Chat
    # def create_chat(self, obj: Any) -> Chat:
    #     return self.create(Chat, obj)

    # async def read_chat(self, id: int) -> Optional[Chat]:
    #     selection = select(Chat).filter(Chat.id == id)
    #     return (await self.fetch(selection)).one_or_none()

    # async def get_chat(self, id: int) -> Chat:
    #     chat = await self.read_chat(id)
    #     if chat is not None:
    #         return chat
    #     return self.create_raw(Chat, id=id)


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
