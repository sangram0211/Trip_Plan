"""
Remote MCP servers, reached over HTTP.

Currently: Tavily (hotel / general web search).
"""

from src.clients.cache import async_cached
from src.config.settings import CACHE_TTL_HOTELS
from src.mcp_servers.config import load_tools, require_tools

SERVER_NAME = "tavily"
SEARCH_TOOL_NAME = "tavily_search"


_search_tool = None


async def _get_search_tool():
    """Connect to Tavily once and keep the search tool handle."""

    global _search_tool

    if _search_tool is not None:
        return _search_tool

    tools = await require_tools(SERVER_NAME, SEARCH_TOOL_NAME)
    _search_tool = tools[SEARCH_TOOL_NAME]
    return _search_tool


@async_cached(ttl=CACHE_TTL_HOTELS)
async def tavily_mcp_search(query: str, max_results: int = 5) -> list:
    """Search the web via Tavily MCP and return a list of results."""
    tool = await _get_search_tool()
    result = await tool.ainvoke({"query": query, "max_results": max_results})
    return result
