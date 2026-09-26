"""Finds hotel options for the destination through the Tavily MCP server."""

from langchain_core.messages import AIMessage

from src.agents.prompts import HOTEL_SEARCH_QUERY
from src.graph.state import TravelState
from src.mcp_servers.remote import tavily_mcp_search
from src.utils.async_utils import bump_llm_calls, run_async


def hotel_agent(state: TravelState):
    print("\nINSIDE HOTEL AGENT\n")

    query = state["user_query"]

    # Build a targeted hotel search query
    search_query = f"best hotels in {query} recommendations reviews booking"

    try:
        results = run_async(tavily_mcp_search(search_query))
        hotel_results = str(results)
    except Exception as e:
        hotel_results = f"Hotel search unavailable: {e}"

    return bump_llm_calls(state, {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content=hotel_results, name="hotel_agent")],
    })
