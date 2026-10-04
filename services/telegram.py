import httpx

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

            except Exception:
                print("[TG] An error has occured")

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

            except httpx.HTTPStatusError:
                print("[TG] HTTP Status Error")

            except httpx.RequestError:
                print("[TG] Request Error")