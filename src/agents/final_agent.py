"""Formats everything the other agents produced into the user-facing answer."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.prompts import FINAL_AGENT_PROMPT, FINAL_SYSTEM_PROMPT
from src.clients.llm import get_llm
from src.graph.state import TravelState
from src.utils.async_utils import bump_llm_calls


def final_agent(state: TravelState):
    prompt = FINAL_AGENT_PROMPT.format(
        user_query=state["user_query"],
        flight_results=state.get("flight_results", ""),
        hotel_results=state.get("hotel_results", ""),
        weather_results=state.get("weather_results", ""),
        itinerary=state.get("itinerary", ""),
        budget_estimate=state.get("budget_estimate", ""),
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=FINAL_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)

    return bump_llm_calls(state, {
        "messages": [AIMessage(content=result.content)],
    })
