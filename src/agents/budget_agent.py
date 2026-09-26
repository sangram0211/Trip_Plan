"""Estimates the trip budget based on destination, duration, and preferences."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.prompts import BUDGET_AGENT_PROMPT, BUDGET_SYSTEM_PROMPT
from src.clients.llm import get_llm
from src.graph.state import TravelState
from src.utils.async_utils import bump_llm_calls


def budget_agent(state: TravelState):
    """Produce a detailed cost breakdown for the planned trip."""
    print("\nINSIDE BUDGET AGENT\n")

    prompt = BUDGET_AGENT_PROMPT.format(
        user_query=state["user_query"],
        flight_results=state.get("flight_results", "Not yet available"),
        hotel_results=state.get("hotel_results", "Not yet available"),
    )

    llm = get_llm()
    messages = [
        SystemMessage(content=BUDGET_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)

    return bump_llm_calls(state, {
        "budget_estimate": result.content,
        "messages": [AIMessage(content=result.content, name="budget_agent")],
    })
