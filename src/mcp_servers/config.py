"""
MCP server registry, split by where the server actually runs.

REMOTE servers are reached over HTTP and are operated by someone else.
LOCAL servers are spawned as child processes over stdio on this machine.
"""

import os
import sys
from functools import lru_cache
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.config.settings import (
    AVIATIONSTACK_API_KEY,
    OPENWEATHER_API_KEY,
    TAVILY_API_KEY,
)

# This package holds the weather server we ship ourselves.
MCP_DIR = Path(__file__).resolve().parent
WEATHER_SERVER_PATH = MCP_DIR / "weather_server.py"


def _child_env(**overrides: str) -> dict:
    """
    Full copy of the current environment plus explicit overrides.

    stdio servers are launched as subprocesses, and on Windows they need
    the complete parent environment (PATH, SystemRoot, ...) to start.
    """

    env = os.environ.copy()
    env.update({key: value or "" for key, value in overrides.items()})

    return env


# =========================
# Remote MCP servers (HTTP)
# =========================

REMOTE_SERVERS = {
    "tavily": {
        "transport": "streamable_http",
        "url": (
            "https://mcp.tavily.com/mcp/"
            f"?tavilyApiKey={TAVILY_API_KEY}"
        ),
    },
}


# =========================
# Local MCP servers (stdio)
# =========================

LOCAL_SERVERS = {
    "aviationstack": {
        "command": "uvx",
        "args": ["aviationstack-mcp"],
        "transport": "stdio",
        "env": _child_env(AVIATIONSTACK_API_KEY=AVIATIONSTACK_API_KEY or ""),
    },
    "weather": {
        "command": sys.executable,
        "args": [str(WEATHER_SERVER_PATH)],
        "transport": "stdio",
        "env": _child_env(OPENWEATHER_API_KEY=OPENWEATHER_API_KEY or ""),
    },
}


@lru_cache(maxsize=None)
def _remote_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(REMOTE_SERVERS)


@lru_cache(maxsize=None)
def _local_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(LOCAL_SERVERS)


async def load_tools(server_name: str) -> dict:
    """Load tools from a named MCP server. Returns a dict keyed by tool name."""
    if server_name in REMOTE_SERVERS:
        client = _remote_client()
    else:
        client = _local_client()

    async with client as c:
        tools = await c.get_tools()
        return {t.name: t for t in tools if t.name}


async def require_tools(server_name: str, *tool_names: str) -> dict:
    """Load tools and raise if any required tool is missing."""
    tools = await load_tools(server_name)
    missing = [n for n in tool_names if n not in tools]
    if missing:
        raise RuntimeError(f"MCP server {server_name!r} is missing tools: {missing}")
    return {n: tools[n] for n in tool_names}
