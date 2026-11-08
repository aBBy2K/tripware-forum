from core.celery_conf import celery
from security.email import send_email

import asyncio
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_mail(self, subject: str, body: str, email: str):
    try:
        asyncio.run(send_email(subject, body, email))
        return {"sent": True}
    except Exception as e:
        logger.exception(f"An exception has occurred while trying to send an email: {e}")
        raise