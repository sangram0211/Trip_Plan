"""
Helpers for calling async MCP tools from the synchronous graph nodes.

app.py applies nest_asyncio, which is what makes asyncio.run() safe to
call from inside FastAPI's already-running event loop.
"""

import asyncio
from typing import Any, Awaitable, TypeVar

T = TypeVar("T")


def run_async(coroutine: Awaitable[T]) -> T:
    """Run a coroutine to completion from synchronous code."""
    return asyncio.run(coroutine)


def bump_llm_calls(state: dict, updates: dict) -> dict:
    """Increment the llm_calls counter and merge updates."""
    return {
        **updates,
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def truncate(text: str, max_chars: int) -> str:
    """Truncate a string to at most max_chars characters."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"
