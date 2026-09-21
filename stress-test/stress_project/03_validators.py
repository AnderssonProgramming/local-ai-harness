"""Input validation helpers."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))

def validate_title(title: str) -> bool:
    return 1 <= len(title.strip()) <= 120

def validate_priority(value: int) -> bool:
    return value in (1, 2, 3, 4)

class ValidationError(Exception):
    pass

def assert_valid_task_payload(payload: dict):
    if not validate_title(payload.get("title", "")):
        raise ValidationError("Title must be 1-120 characters")
    if "priority" in payload and not validate_priority(payload["priority"]):
        raise ValidationError("Priority must be between 1 and 4")
