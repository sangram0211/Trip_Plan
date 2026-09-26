"""Fetches current weather and forecast for the extracted destination."""

from langchain_core.messages import AIMessage

from src.agents.prompts import WEATHER_RESULTS_TEMPLATE
from src.graph.state import TravelState
from src.agents.destination import extract_destination
from src.mcp_servers.local import forecast_mcp_search, weather_mcp_search
from src.utils.async_utils import run_async


def weather_agent(state: TravelState):
    print("\nINSIDE WEATHER AGENT\n")

    query = state["user_query"]

    try:
        destination = extract_destination(query)
    except Exception:
        destination = query

    try:
        current = run_async(weather_mcp_search(destination))
        current_str = str(current)
    except Exception as e:
        current_str = f"Current weather unavailable: {e}"

    try:
        forecast = run_async(forecast_mcp_search(destination))
        forecast_str = str(forecast)
    except Exception as e:
        forecast_str = f"Forecast unavailable: {e}"

    weather_results = WEATHER_RESULTS_TEMPLATE.format(
        current=current_str,
        forecast=forecast_str,
        advice="pack accordingly and check local advisories before travel.",
    )

    return {
        "weather_results": weather_results,
        "messages": [AIMessage(content=weather_results, name="weather_agent")],
    }
