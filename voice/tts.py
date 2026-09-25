import asyncio


async def speak(text: str) -> None:
    process = await asyncio.create_subprocess_exec("espeak-ng", text)
    await process.wait()
