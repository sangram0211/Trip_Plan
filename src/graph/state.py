"""Shared state passed between every node of the trip planning graph."""

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage


class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    weather_results: str
    itinerary: str
    budget_estimate: str   # added: dedicated budget breakdown
    llm_calls: int
