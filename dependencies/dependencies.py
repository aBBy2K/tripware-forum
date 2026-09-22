from functools import lru_cache
import config
from services.moderation import ModerationService

@lru_cache
def get_moderation_service() -> ModerationService:
    return ModerationService(api_key=config.GROQ_API_KEY)