from typing import Any, Awaitable, Callable, Dict, Type, TypeVar

T = TypeVar("T", bound=Any)
Func = Callable[[T, str], Awaitable[None]]
MapToFunc = Dict[Type[T], Func]


_reply_functions: MapToFunc = {}


def reply_function(type: Type[Any]) -> Callable[[Func], Func]:
    def inner(f: Func) -> Func:
        _reply_functions[type] = f
        return f

    return inner


async def reply_to(msg: Any, text: str) -> None:
    await _reply_functions[type(msg)](msg, text)


_answer_functions: MapToFunc = {}


def answer_function(type: Type[Any]) -> Callable[[Func], Func]:
    def inner(f: Func) -> Func:
        _answer_functions[type] = f
        return f

    return inner


async def answer_to(msg: Any, text: str) -> None:
    await _answer_functions[type(msg)](msg, text)


class Messenger:
    target_message: Any = None

    async def send(self, text: str) -> None:
        await answer_to(self.target_message, text)
