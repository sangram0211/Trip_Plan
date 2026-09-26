"""Combines flight, hotel, weather and budget results into a day-by-day itinerary."""

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.prompts import ITINERARY_AGENT_PROMPT, ITINERARY_SYSTEM_PROMPT
from src.clients.llm import get_llm
from src.graph.state import TravelState
from src.utils.async_utils import bump_llm_calls


def itinerary_agent(state: TravelState):
    prompt = ITINERARY_AGENT_PROMPT.format(
        user_query=state["user_query"],
        flight_results=state.get("flight_results", ""),
        hotel_results=state.get("hotel_results", ""),
        weather_results=state.get("weather_results", ""),
        budget_estimate=state.get("budget_estimate", ""),
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)

    return bump_llm_calls(state, {
        "itinerary": result.content,
    })
