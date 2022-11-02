import re
from typing import Any, Awaitable, Callable, Dict, Protocol, Type, TypeVar

from .database import DataBase
from .models import Message

T = TypeVar("T", bound=Any)
SendFunc = Callable[[T, str, bool], Awaitable[None]]
MapToFunc = Dict[Type[T], SendFunc]
CommandHandler = Callable[["Bot", str], Awaitable[None]]


# COMMAND_REGEXP = r"(?:/(?P<command>\w+) )?\s*(?P<text>.+)"
# COMMAND_REGEXP = r"(?:/(\w+)\s*)?(.+)"
COMMAND_REGEXP = r"(?:/(\S+))? *(.*)"
COMMAND_PATTERN = re.compile(COMMAND_REGEXP)


class Bot:
    db: DataBase
    msg: Message
    target_message: Any = None

    send_functions: MapToFunc = {}

    def send_function(self, type: Type[Any]) -> Callable[[SendFunc], SendFunc]:
        def inner(f: SendFunc) -> SendFunc:
            self.send_functions[type] = f
            return f

        return inner

    async def send(self, text: str, mention: bool = False) -> None:
        msg = self.target_message
        await self.send_functions[type(msg)](msg, text, mention)

    commands: Dict[str, CommandHandler] = {}

    def command(self, *names: str) -> Callable[[CommandHandler], CommandHandler]:
        def inner(f: CommandHandler) -> CommandHandler:
            for name in names:
                self.commands[name] = f
            return f

        return inner

    async def handle_message(self, db: DataBase, in_msg: Any, msg: Message) -> None:
        self.target_message = in_msg
        self.db = db
        self.msg = msg

        match = COMMAND_PATTERN.match(msg.text)
        if match is None:
            return
        command, text = match.groups()

        func = self.commands.get(command)
        if func is not None:
            await func(self, text)


bot = Bot()
