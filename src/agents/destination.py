"""Extracts the destination city/country from the user query."""

from langchain_core.messages import HumanMessage, SystemMessage

from src.clients.llm import get_llm


def extract_destination(user_query: str) -> str:
    """
    Use the LLM to extract the primary destination from a travel query.
    Returns a simple string like 'Paris, France' or 'Tokyo, Japan'.
    """
    llm = get_llm()
    messages = [
        SystemMessage(content="Extract the primary travel destination from the user query. Return only the city and country name, nothing else. Example: 'Paris, France'"),
        HumanMessage(content=user_query),
    ]
    result = llm.invoke(messages)
    return result.content.strip()
