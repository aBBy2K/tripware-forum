from datetime import datetime
from .template_config import template

def last_seen(value: datetime) -> str:
    now = datetime.now()
    diff = int((now - value).total_seconds())

    now = datetime.now()
    diff = int((now - value).total_seconds())
    if diff < 60:
        return "just now"
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    return f"{diff // 86400}d ago"


template.env.filters["last_seen"] = last_seen