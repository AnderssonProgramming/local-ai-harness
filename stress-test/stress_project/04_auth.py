"""Minimal auth decorator for route handlers."""
import functools

_SESSIONS = {}

def create_session(user_id: int, token: str):
    _SESSIONS[token] = user_id

def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(token, *args, **kwargs):
        if token not in _SESSIONS:
            raise PermissionError("Invalid or expired session token")
        return fn(_SESSIONS[token], *args, **kwargs)
    return wrapper

def revoke_session(token: str):
    _SESSIONS.pop(token, None)
