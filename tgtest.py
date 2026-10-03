import asyncio
from services.telegram import TelegramService

async def main():
    ok = await TelegramService.get_updates(None, 30)
    print(ok)

asyncio.run(main())