"""Minimal OpenWeatherMap MCP server (stdio transport)."""

import asyncio
import json
import os
import sys

import requests

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
BASE_URL = "https://api.openweathermap.org/data/2.5"


def get_current_weather(location: str) -> dict:
    """Fetch current weather for a location."""
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY not set"}

    try:
        response = requests.get(
            f"{BASE_URL}/weather",
            params={
                "q": location,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=10,
        )
        data = response.json()
        if response.status_code == 200:
            return {
                "location": location,
                "temperature": f"{data['main']['temp']}°C",
                "feels_like": f"{data['main']['feels_like']}°C",
                "humidity": f"{data['main']['humidity']}%",
                "description": data['weather'][0]['description'],
                "wind_speed": f"{data['wind']['speed']} m/s",
            }
        return {"error": data.get("message", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}


def get_forecast(location: str) -> dict:
    """Fetch 5-day weather forecast for a location."""
    if not OPENWEATHER_API_KEY:
        return {"error": "OPENWEATHER_API_KEY not set"}

    try:
        response = requests.get(
            f"{BASE_URL}/forecast",
            params={
                "q": location,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "cnt": 8,  # Next 24 hours in 3h intervals
            },
            timeout=10,
        )
        data = response.json()
        if response.status_code == 200:
            forecasts = []
            for item in data.get("list", []):
                forecasts.append({
                    "time": item["dt_txt"],
                    "temp": f"{item['main']['temp']}°C",
                    "description": item["weather"][0]["description"],
                })
            return {"location": location, "forecast": forecasts}
        return {"error": data.get("message", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}


# Simple stdio MCP server implementation
TOOLS = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather for a given location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or location"}
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_forecast",
        "description": "Get weather forecast for a given location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or location"}
            },
            "required": ["location"],
        },
    },
]


def handle_request(request: dict) -> dict:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "weather", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "get_current_weather":
            result = get_current_weather(arguments.get("location", ""))
        elif tool_name == "get_forecast":
            result = get_forecast(arguments.get("location", ""))
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result)}]
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}), flush=True)
