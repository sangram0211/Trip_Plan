"""Every prompt template used by the trip planning agents."""

FLIGHT_SYSTEM_PROMPT = "You are an expert travel flight planner with deep knowledge of global aviation."

FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Provide detailed flight guidance including:

1. Likely departure airport (with IATA code)
2. Likely arrival airport (with IATA code)
3. Airlines serving this route
4. Typical flight duration and number of stops
5. Estimated airfare range (economy & business)
6. Peak season pricing warning if applicable
7. Best booking time advice
8. Alternative routing options if available

Return concise, actionable travel guidance.
"""


HOTEL_SEARCH_QUERY = "{destination} best hotels {budget} budget {dates}"


WEATHER_RESULTS_TEMPLATE = """
Current Weather: {current}
Forecast: {forecast}
Travel Advice: Based on the weather, {advice}
"""


ITINERARY_SYSTEM_PROMPT = "You are an expert trip planner who creates practical, enjoyable day-by-day itineraries."

ITINERARY_AGENT_PROMPT = """
Create a complete travel itinerary for the following trip.

User Query:
{user_query}

Flight Results:
{flight_results}

Hotel Results:
{hotel_results}

Weather Results:
{weather_results}

Budget Estimate:
{budget_estimate}

Create a practical, day-by-day itinerary that:
- Accounts for the flight schedule
- Balances popular attractions with local hidden gems
- Groups activities by location to minimise travel time
- Suggests specific restaurants and meal options
- Includes estimated time for each activity
- Is mindful of the budget
"""


BUDGET_SYSTEM_PROMPT = "You are an expert travel budget analyst with up-to-date knowledge of travel costs worldwide."

BUDGET_AGENT_PROMPT = """
Create a detailed budget estimate for this trip.

User Query:
{user_query}

Flight Results:
{flight_results}

Hotel Results:
{hotel_results}

Provide a breakdown including:
1. Flights (economy / business estimate)
2. Accommodation (per night x number of nights)
3. Local transport (airport transfers, city travel)
4. Food & dining (per day estimate x days)
5. Activities & entrance fees
6. Miscellaneous & travel insurance
7. **Total estimated budget** (budget / mid-range / luxury tiers)

Be specific with currency amounts and ranges.
"""


FINAL_SYSTEM_PROMPT = "You are a professional AI trip planner who creates beautifully formatted, comprehensive travel plans."

FINAL_AGENT_PROMPT = """
Create a comprehensive, beautifully formatted trip plan.

User Query:
{user_query}

Flight Information:
{flight_results}

Hotel Options:
{hotel_results}

Weather Outlook:
{weather_results}

Day-by-Day Itinerary:
{itinerary}

Budget Breakdown:
{budget_estimate}

Format the response as a complete trip plan with clear sections, emoji icons for readability, and practical tips throughout. End with 3 key travel tips specific to this destination.
"""
