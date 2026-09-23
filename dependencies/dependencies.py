from functools import lru_cache
import config
from services.moderation import ModerationService
from services.gpt import GPTService

@lru_cache
def get_moderation_service() -> ModerationService:
    return ModerationService(api_key=config.GROQ_API_KEY)

@lru_cache
def get_gpt_service() -> GPTService:
    return GPTService(api_key=config.GROQ_API_KEY)