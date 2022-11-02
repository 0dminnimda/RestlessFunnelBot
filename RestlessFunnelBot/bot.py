import re
from typing import Any, Awaitable, Callable, Dict, Optional, Type, TypeVar

from .database import DataBase
from .models import Message

T = TypeVar("T", bound=Any)
SendFunc = Callable[[T, str, bool, bool], Awaitable[None]]
MapToFunc = Dict[Type[T], SendFunc]

CommandHandler = Callable[["Bot", str], Awaitable[None]]
CommandMap = Dict[str, CommandHandler]


COMMAND_REGEXP = r"(?:/(\S+))? *(.*)"
DEFAULT_COMMAND = chr(1).join("$default$")


class Bot:
    db: DataBase
    msg: Message
    target_message: Any
    command_pattern: re.Pattern

    def __init__(self) -> None:
        self.target_message = None
        self.command_pattern = re.compile(COMMAND_REGEXP)
        self.default_handler = None

    send_functions: MapToFunc = {}

    def send_function(self, type: Type[Any]) -> Callable[[SendFunc], SendFunc]:
        def inner(f: SendFunc) -> SendFunc:
            self.send_functions[type] = f
            return f

        return inner

    async def send(self, text: str, mention: bool = False, raw: bool = False) -> None:
        msg = self.target_message
        await self.send_functions[type(msg)](msg, text, mention, raw)

    commands: CommandMap = {}
    default_handler: Optional[CommandHandler]

    def command(self, *names: str) -> Callable[[CommandHandler], CommandHandler]:
        def inner(f: CommandHandler) -> CommandHandler:
            for name in names:
                self.commands[name] = f
                if name == DEFAULT_COMMAND:
                    self.default_handler = f
            return f

        return inner

    async def handle_message(self, db: DataBase, in_msg: Any, msg: Message) -> None:
        self.target_message = in_msg
        self.db = db
        self.msg = msg

        match = self.command_pattern.match(msg.text)

        if match is None:
            text = msg.text
            func = self.default_handler
        else:
            command, text = match.groups()
            func = self.commands.get(command, self.default_handler)

        if func is not None:
            await func(self, text)


bot = Bot()
