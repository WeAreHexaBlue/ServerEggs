import asyncio
from typing import Any

from jishaku.repl import AsyncCodeExecutor, Scope, wrap_code


def validate_presence(code: str) -> None:
    wrap_code(code)

def executor(bot, code: str) -> AsyncCodeExecutor:
    return AsyncCodeExecutor(
        code,
        scope=Scope(),
        arg_dict={"_bot": bot},
        loop=asyncio.get_running_loop(),
    )

async def run_code(bot, code: str) -> str:
    async def execute() -> str:
        result: Any = None
        async for result in executor(bot, code):
            pass

        return str(result)

    return await asyncio.wait_for(execute(), 10)

async def run_presence(bot, presence) -> str:
    if not presence.code:
        return presence.text

    return await run_code(bot, presence.code)