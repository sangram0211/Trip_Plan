"""Turns the user query into concrete flight guidance using AviationStack MCP."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.prompts import FLIGHT_AGENT_PROMPT, FLIGHT_SYSTEM_PROMPT
from src.clients.llm import get_llm
from src.config.settings import (
    AIRLINE_DATA_CHAR_LIMIT,
    AIRPORT_DATA_CHAR_LIMIT,
)
from src.graph.state import TravelState
from src.mcp_servers.local import aviation_mcp_call
from src.utils.async_utils import bump_llm_calls, run_async, truncate


def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:
        airports = run_async(aviation_mcp_call("list_airports", {}))
        airport_data = truncate(str(airports), AIRPORT_DATA_CHAR_LIMIT)
    except Exception as e:
        airport_data = f"Airport data unavailable: {e}"

    try:
        airlines = run_async(aviation_mcp_call("list_airlines", {}))
        airline_data = truncate(str(airlines), AIRLINE_DATA_CHAR_LIMIT)
    except Exception as e:
        airline_data = f"Airline data unavailable: {e}"

    prompt = FLIGHT_AGENT_PROMPT.format(
        query=query,
        airport_data=airport_data,
        airline_data=airline_data,
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=FLIGHT_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)

    return bump_llm_calls(state, {
        "flight_results": result.content,
        "messages": [AIMessage(content=result.content, name="flight_agent")],
    })
