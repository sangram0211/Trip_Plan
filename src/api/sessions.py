"""
In-memory store for credentials a user typed into the settings panel.

Deliberately NOT backed by Redis or PostgreSQL: these are live API keys and
database URLs, and this store is the one place they exist on the server.
Keeping them in process memory means they are never written to disk, never
replicated, and are gone when the process restarts.
"""

import secrets
import threading
import time

from src.config.session import Credentials

SESSION_COOKIE = "tripplanner_session"

# How long an idle session keeps its keys.
SESSION_TTL_SECONDS = 12 * 3600

# Guard against unbounded growth from repeated cookie-less requests.
MAX_SESSIONS = 500


_lock = threading.Lock()
_sessions: dict[str, dict] = {}


def new_session_id() -> str:
    return secrets.token_urlsafe(24)


def _prune(now: float) -> None:
    """Caller must hold the lock."""

    expired = [
        sid for sid, entry in _sessions.items()
        if entry["expires_at"] <= now
    ]

    for sid in expired:
        del _sessions[sid]

    if len(_sessions) > MAX_SESSIONS:
        oldest = sorted(_sessions, key=lambda sid: _sessions[sid]["expires_at"])
        for sid in oldest[:len(_sessions) - MAX_SESSIONS]:
            del _sessions[sid]


def store_credentials(session_id: str, credentials: Credentials) -> None:
    now = time.time()
    with _lock:
        _prune(now)
        _sessions[session_id] = {
            "credentials": credentials,
            "expires_at":  now + SESSION_TTL_SECONDS,
        }


def get_credentials_for(session_id: str) -> Credentials | None:
    now = time.time()
    with _lock:
        entry = _sessions.get(session_id)
        if entry is None or entry["expires_at"] <= now:
            return None
        # Refresh TTL on access.
        entry["expires_at"] = now + SESSION_TTL_SECONDS
        return entry["credentials"]


def clear_credentials(session_id: str) -> None:
    with _lock:
        _sessions.pop(session_id, None)
