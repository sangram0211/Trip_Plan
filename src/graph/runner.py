"""Entry point the API layer calls to run one trip planning request."""

import uuid

from src.config.session import require
from src.graph.graph import get_travel_graph
from src.graph.state import TravelState


def initial_state(user_input: str) -> dict:
    return {
        "messages": [],
        "user_query": user_input,
        "flight_results": "",
        "hotel_results": "",
        "weather_results": "",
        "itinerary": "",
        "budget_estimate": "",
        "llm_calls": 0,
    }


def run_travel_agent(user_input: str, thread_id: str | None = None) -> dict:
    # Check everything up front so the caller learns about every missing key
    # at once, rather than one per failed attempt.
    require("GROQ_API_KEY", "DATABASE_URL")

    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = get_travel_graph().invoke(
        initial_state(user_input),
        config=config,
    )

    result["thread_id"] = thread_id
    return result
