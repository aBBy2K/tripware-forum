from json import JSONDecodeError, loads
import json
from httpx import HTTPError
import httpx

class GPTService:
    def __init__(self, api_key: str):
        self.client = httpx.AsyncClient(
            base_url="https://api.groq.com/openai/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    async def generate_text_response(self, prompt: str, history: list[dict]) -> dict:
        messages = [
            {
                "role": "system",
                "content": """Ты — дружелюбный ИИ-ассистент форума. Отвечай на языке, на котором пишет пользователь.
                Ты не можешь генерировать изображения и подобное — твоя задача просто отвечать на сообщения пользователя.
                Поддерживай дружескую атмосферу в чате, отвечай покороче.

                Ответь ТОЛЬКО JSON: {"response": "текст ответа"}"""
            }
        ]

        messages += history
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.post("/chat/completions", json={
                "model": "openai/gpt-oss-20b",
                "response_format": {"type": "json_object"},
                "max_tokens": 500,
                "reasoning_effort": "low",
                "messages": messages,
            })
            response.raise_for_status()

            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw)

            return {
                "failure": False,
                "response": parsed["response"],
            }

        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
            print(f"AI text generation failed: {e}")
            return {
                "failure": True,
                "response": None,
            }

    async def random_fact_cb(self) -> dict:
        try:
            response = await self.client.post("/chat/completions", json={
                "model": "openai/gpt-oss-20b",
                "response_format": {"type": "json_object"},
                "max_tokens": 500,
                "reasoning_effort": "low",
                "messages": [{
                    "role": "user",
                    "content": """Сгенерируй рандомный не длинный но и не короткий факт о чем угодно
                    
                    Ответь ТОЛЬКО JSON: {"response": ответ}
                    """
                }]
            })
            response.raise_for_status()

            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw)

            return {
                "failure": False,
                "response": parsed["response"],
            }
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
            print(f"AI random fact generation failed: {e}")
            return {
                "failure": True,
                "response": None,
            }
