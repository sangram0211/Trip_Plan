<h1 align="center">Trip Planner AI</h1>

<p align="center">
  <img src="https://img.shields.io/badge/status-active-22c55e.svg" alt="Status">
  <a href="https://github.com/sangram0211/Trip_Plan/issues"><img src="https://img.shields.io/github/issues/sangram0211/Trip_Plan.svg" alt="GitHub Issues"></a>
  <a href="https://github.com/sangram0211/Trip_Plan/pulls"><img src="https://img.shields.io/github/issues-pr/sangram0211/Trip_Plan.svg" alt="GitHub Pull Requests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue.svg" alt="License"></a>
</p>

---

<p align="center">A multi-agent AI trip planner. Describe the trip you want in
    plain English and get back flights, hotels, weather, a day-by-day
    itinerary and a budget estimate — researched for you in about a minute.
    <br>
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [Authors](#authors)

## 🧐 About <a name = "about"></a>

Planning a trip usually means juggling half a dozen browser tabs — one for flights, another for hotels, a third for the weather, and a notes app where you try to fit it all into a sensible order. **Trip Planner AI** collapses that into a single conversation.

You describe the trip you want in your own words — *"Plan a 10 day Europe trip from India in April, mid-range budget"* — and a team of AI specialists goes and researches it. One looks into flights, another finds places to stay, another checks the weather. A dedicated budget agent then estimates costs. Their findings are pulled together into a complete plan you can actually act on.

| | |
|---|---|
| ✈️ **Flights** | Likely airports, airlines on the route, typical duration and fare range |
| 🏨 **Hotels** | Accommodation options matched to your destination and budget |
| 🌤️ **Weather** | Current conditions and the forecast, with travel advice |
| 🗺️ **Itinerary** | A realistic day-by-day plan you can actually follow |
| 💰 **Budget** | A detailed breakdown of estimated trip costs |

Plans are saved as you go, so you can reopen a trip later and ask follow-up
questions without starting over.

## 🏁 Getting Started <a name = "getting_started"></a>

### Prerequisites

- **Python 3.11**
- **[uv](https://docs.astral.sh/uv/)** — for dependency management
- **A PostgreSQL database** — a free [Render](https://render.com/) instance works fine
- **API keys** (all have free tiers):
  - [Groq](https://console.groq.com/)
  - [Tavily](https://tavily.com/)
  - [AviationStack](https://aviationstack.com/)
  - [OpenWeather](https://openweathermap.org/api)

### Installing

```bash
git clone https://github.com/sangram0211/Trip_Plan.git
cd Trip_Plan
```

Install dependencies:

```bash
uv sync
```

Create `.env`:

```dotenv
GROQ_API_KEY=your_groq_key
DATABASE_URL=postgresql://user:password@host:5432/dbname
TAVILY_API_KEY=your_tavily_key
AVIATIONSTACK_API_KEY=your_aviationstack_key
OPENWEATHER_API_KEY=your_openweather_key
```

## 🚀 Usage <a name = "usage"></a>

```bash
uv run uvicorn app:app --reload
```

Open http://localhost:8000 and start planning!

## 🏗️ Architecture <a name = "architecture"></a>

The system uses a LangGraph state machine with 5 parallel specialist agents:

```
User Query
    │
    ├── Flight Agent   (AviationStack MCP)
    ├── Hotel Agent    (Tavily MCP)
    ├── Weather Agent  (OpenWeather MCP)
    ├── Budget Agent   (LLM estimation)
    └── Itinerary Agent
            │
        Final Agent → Formatted Response
```

## ✍️ Authors <a name = "authors"></a>

- [@sangram0211](https://github.com/sangram0211)
