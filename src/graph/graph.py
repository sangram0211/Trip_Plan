"""Wires the agents together into the LangGraph workflow."""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from src.agents.final_agent import final_agent
from src.agents.flight_agent import flight_agent
from src.agents.hotel_agent import hotel_agent
from src.agents.itinerary_agent import itinerary_agent
from src.agents.weather_agent import weather_agent
from src.agents.budget_agent import budget_agent
from src.clients.checkpointer import get_checkpointer
from src.config.session import require, resolve_database_url
from src.graph.state import TravelState


def build_graph() -> StateGraph:
    g = StateGraph(TravelState)

    # Specialist nodes run in parallel (LangGraph fans them out)
    g.add_node("flight_agent",    flight_agent)
    g.add_node("hotel_agent",     hotel_agent)
    g.add_node("weather_agent",   weather_agent)
    g.add_node("budget_agent",    budget_agent)

    # Itinerary synthesises the specialist results
    g.add_node("itinerary_agent", itinerary_agent)

    # Final agent formats everything for the user
    g.add_node("final_agent",     final_agent)

    # Fan out from START
    g.add_edge(START, "flight_agent")
    g.add_edge(START, "hotel_agent")
    g.add_edge(START, "weather_agent")
    g.add_edge(START, "budget_agent")

    # All specialists feed into itinerary
    g.add_edge("flight_agent",  "itinerary_agent")
    g.add_edge("hotel_agent",   "itinerary_agent")
    g.add_edge("weather_agent", "itinerary_agent")
    g.add_edge("budget_agent",  "itinerary_agent")

    g.add_edge("itinerary_agent", "final_agent")
    g.add_edge("final_agent", END)

    return g


@lru_cache(maxsize=4)
def _compiled_graph(database_url: str):
    checkpointer = get_checkpointer(database_url)
    return build_graph().compile(checkpointer=checkpointer)


def get_travel_graph():
    require("GROQ_API_KEY", "DATABASE_URL")
    db_url = resolve_database_url()
    return _compiled_graph(db_url)
