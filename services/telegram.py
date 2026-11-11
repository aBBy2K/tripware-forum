import httpx
import logging

logger = logging.getLogger(__name__)
from config import TG_BOT_TOKEN

class TelegramService:
    @staticmethod
    async def send_message(text, chat_id):
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

        async with httpx.AsyncClient(timeout=5) as client:
            try:
                response = await client.post(
                    url,
                    json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
                )

                response.raise_for_status()

                return True

            except Exception as e:
                logger.exception(f"An error has occured: {e}")

    @staticmethod
    async def get_updates(offset, timeout):
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getUpdates"

        json_to_send = {"timeout": timeout}

        if offset is not None:
            json_to_send["offset"] = offset

        async with httpx.AsyncClient(timeout=timeout + 10) as client: 
            try:
                response = await client.post(
                    url,
                    json=json_to_send
                )

                response.raise_for_status()

                data = response.json()

                if data["ok"]:
                    return data["result"]

            except httpx.HTTPStatusError as e:
                logger.exception(f"[TG] HTTP Status Error: {e}")

            except httpx.RequestError as e:
                logger.exception(f"[TG] Request Error: {e}")