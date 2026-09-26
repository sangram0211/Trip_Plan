"""
Per-session credentials.

Keys can come from two places:

* the server's .env  - shared by everyone, set once at deploy time
* the browser session - typed into the settings panel, held in memory only

Session values take precedence, are never written to disk, and disappear
when the session expires. Resolution happens through a ContextVar so the
agents can stay unaware of where a key came from.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from src.config import settings


@dataclass(frozen=True)
class Credentials:
    groq_api_key: str | None = None
    database_url: str | None = None


EMPTY = Credentials()

_current: ContextVar[Credentials] = ContextVar("tripplanner_credentials", default=EMPTY)


class MissingCredentialsError(RuntimeError):
    """Raised when a required key is configured in neither .env nor the session."""

    def __init__(self, missing: list[str]):
        self.missing = missing

        super().__init__(
            "Missing credentials: "
            + ", ".join(missing)
            + ". Add them in Settings, or set them in the server's .env file."
        )


def get_credentials() -> Credentials:
    return _current.get()


@contextmanager
def use_credentials(credentials: Credentials | None):
    """Bind session credentials for the duration of one request."""
    token = _current.set(credentials or EMPTY)
    try:
        yield
    finally:
        _current.reset(token)


def require(*keys: str) -> None:
    """Raise MissingCredentialsError if any of the given keys are absent."""
    creds = get_credentials()
    missing = [k for k in keys if not _resolve(k, creds)]
    if missing:
        raise MissingCredentialsError(missing)


def _resolve(key: str, creds: Credentials) -> str | None:
    """Session value takes precedence over the .env value."""
    session_val = getattr(creds, key.lower(), None)
    if session_val:
        return session_val
    return getattr(settings, key, None)


def resolve_groq_api_key(creds: Credentials | None = None) -> str | None:
    c = creds or get_credentials()
    return c.groq_api_key or settings.GROQ_API_KEY


def resolve_database_url(creds: Credentials | None = None) -> str | None:
    c = creds or get_credentials()
    return c.database_url or settings.DATABASE_URL


# ------------------------------------------------------------------
# credential_status — used by GET /api/config
# ------------------------------------------------------------------

_CREDENTIAL_DEFS = [
    {
        "key":   "GROQ_API_KEY",
        "label": "Groq API key",
        "hint":  "Used to call the language model. Get one free at console.groq.com.",
    },
    {
        "key":   "DATABASE_URL",
        "label": "PostgreSQL connection string",
        "hint":  (
            "Used by LangGraph to persist conversation threads. "
            "A free Render.com instance works fine."
        ),
    },
]


def credential_status(session_creds: Credentials | None) -> dict:
    """
    Return the payload that GET /api/config sends to the browser.

    Structure::

        {
          ready: bool,
          missing: ["GROQ_API_KEY", ...],
          credentials: {
            GROQ_API_KEY: { label, hint, source },
            ...
          }
        }

    ``source`` is ``"env"``, ``"session"`` or ``None``.
    """

    creds = session_creds or EMPTY
    result: dict = {"credentials": {}, "missing": [], "ready": False}

    for defn in _CREDENTIAL_DEFS:
        key   = defn["key"]
        label = defn["label"]
        hint  = defn["hint"]

        env_val     = getattr(settings, key, None)
        session_val = getattr(creds, key.lower(), None)

        if session_val:
            source = "session"
        elif env_val:
            source = "env"
        else:
            source = None
            result["missing"].append(key)

        result["credentials"][key] = {"label": label, "hint": hint, "source": source}

    result["ready"] = len(result["missing"]) == 0
    return result
