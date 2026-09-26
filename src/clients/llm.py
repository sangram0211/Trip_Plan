"""Groq chat model, resolved per session and cached per distinct key."""

from functools import lru_cache

from langchain_groq import ChatGroq

from src.config.session import require, resolve_groq_api_key
from src.config.settings import GROQ_MODEL


@lru_cache(maxsize=8)
def _build_llm(model: str, api_key: str) -> ChatGroq:
    return ChatGroq(model=model, api_key=api_key)


def get_llm() -> ChatGroq:
    """Return a ChatGroq instance bound to the current session's API key."""
    require("GROQ_API_KEY")
    api_key = resolve_groq_api_key()
    return _build_llm(GROQ_MODEL, api_key)
