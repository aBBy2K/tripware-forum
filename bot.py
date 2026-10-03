from services.account import AccountService
from services.telegram import TelegramService
import asyncio

async def handle_update(update):
    message = update.get("message")
    if not message:
        return

    text = message.get("text")
    if not text:
        return

    chat = message.get("chat")
    if chat["type"] != "private":
        return

    parts = text.split(maxsplit=1)
    command = parts[0]
    chat_id = chat["id"]

    if command != "/start":
        await TelegramService.send_message("Use this command to link your telegram account with tripware: /start *token*", chat_id)
        return

    if len(parts) < 2:
        await TelegramService.send_message("Use this command to link your telegram account with tripware: /start *token*", chat_id)
        return

    token = parts[1]

    await AccountService.tglink(token, chat_id)

async def main():
    offset = None
    timeout = 30

    while True:
        try:
            updates = await TelegramService.get_updates(offset, timeout)

            if updates is None:
                await asyncio.sleep(5)
                continue

            for update in updates:
                offset = update["update_id"] + 1

                await handle_update(update)

        except Exception as e:
            print(e)

if __name__ == "__main__":
    asyncio.run(main())