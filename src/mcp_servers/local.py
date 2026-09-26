"""
Local MCP servers, spawned as stdio child processes.

* aviationstack - third party server run via `uvx aviationstack-mcp`
* weather       - our own server in this package (weather_server.py)
"""

from src.clients.cache import async_cached
from src.config.settings import (
    CACHE_TTL_AIRLINES,
    CACHE_TTL_AIRPORTS,
    CACHE_TTL_FORECAST,
    CACHE_TTL_WEATHER,
)
from src.mcp_servers.config import (
    WEATHER_SERVER_PATH,
    load_tools,
    require_tools,
)

AVIATION_SERVER_NAME = "aviationstack"
WEATHER_SERVER_NAME = "weather"

CURRENT_WEATHER_TOOL = "get_current_weather"
FORECAST_TOOL = "get_forecast"


# Reference data that effectively never changes, so it is worth a long TTL.
LONG_LIVED_AVIATION_TOOLS = {
    "list_airports": CACHE_TTL_AIRPORTS,
    "list_airlines": CACHE_TTL_AIRLINES,
}


# =========================
# AviationStack
# =========================

_aviation_tools: dict = {}


async def _get_aviation_tools() -> dict:
    global _aviation_tools

    if _aviation_tools:
        return _aviation_tools

    tools = await load_tools(AVIATION_SERVER_NAME)

    if not tools:
        raise RuntimeError(
            "AviationStack MCP connected but returned no tools. "
            "Check that the AVIATIONSTACK_API_KEY is set."
        )

    _aviation_tools = tools
    return tools


async def aviation_mcp_call(tool_name: str, args: dict):
    """Call an AviationStack MCP tool, using the cache for long-lived data."""
    tools = await _get_aviation_tools()

    if tool_name not in tools:
        raise ValueError(f"AviationStack MCP has no tool {tool_name!r}")

    tool = tools[tool_name]
    return await tool.ainvoke(args)


# =========================
# Weather (OpenWeatherMap)
# =========================

_weather_tools: dict = {}


async def _get_weather_tools() -> dict:
    global _weather_tools

    if _weather_tools:
        return _weather_tools

    tools = await load_tools(WEATHER_SERVER_NAME)

    if not tools:
        raise RuntimeError(
            "Weather MCP connected but returned no tools. "
            "Check that OPENWEATHER_API_KEY is set."
        )

    _weather_tools = tools
    return tools


@async_cached(ttl=CACHE_TTL_WEATHER)
async def weather_mcp_search(location: str) -> str:
    """Get current weather for a location."""
    tools = await _get_weather_tools()
    if CURRENT_WEATHER_TOOL not in tools:
        return "Current weather tool not available."
    tool = tools[CURRENT_WEATHER_TOOL]
    result = await tool.ainvoke({"location": location})
    return str(result)


@async_cached(ttl=CACHE_TTL_FORECAST)
async def forecast_mcp_search(location: str) -> str:
    """Get weather forecast for a location."""
    tools = await _get_weather_tools()
    if FORECAST_TOOL not in tools:
        return "Forecast tool not available."
    tool = tools[FORECAST_TOOL]
    result = await tool.ainvoke({"location": location})
    return str(result)
