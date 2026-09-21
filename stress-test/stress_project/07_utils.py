"""Misc helpers used across the app."""
from datetime import datetime, timedelta

def format_relative(dt: datetime) -> str:
    delta = datetime.utcnow() - dt
    if delta < timedelta(minutes=1):
        return "just now"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() // 60)}m ago"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() // 3600)}h ago"
    return f"{delta.days}d ago"

def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def slugify(text: str) -> str:
    return "-".join(text.lower().split())
