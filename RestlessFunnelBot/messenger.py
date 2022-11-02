from typing import Any, Awaitable, Callable, Dict, Type, TypeVar, Protocol


# T = TypeVar("T", bound=Any, contravariant=True)


# class Func(Protocol[T]):
#     async def __call__(self, msg: T, text: str, mention: bool = ...) -> None:
#         ...


T = TypeVar("T", bound=Any)
Func = Callable[[T, str, bool], Awaitable[None]]
MapToFunc = Dict[Type[T], Func]


_send_functions: MapToFunc = {}


def send_function(type: Type[Any]) -> Callable[[Func], Func]:
    def inner(f: Func) -> Func:
        _send_functions[type] = f
        return f

    return inner


async def send(msg: Any, text: str, mention: bool = False) -> None:
    await _send_functions[type(msg)](msg, text, mention)


class Messenger:
    target_message: Any = None

    async def send(self, text: str, mention: bool = False) -> None:
        await send(self.target_message, text, mention)
