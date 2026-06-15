from src.config.settings import Settings
from src.state.travel_state import TravelState
from src.tools import fallback_data
from src.tools.policy import run_tool_with_policy


def search_attractions(state: TravelState, settings: Settings, query: dict) -> list[dict]:
    return run_tool_with_policy(
        state=state,
        settings=settings,
        tool_name="Tavily Attractions",
        required_key="TAVILY_API_KEY",
        live_call=lambda: _search_tavily(settings, query),
        fallback_call=lambda: fallback_data.DEMO_ATTRACTIONS,
        input_summary=f"Attractions for {query.get('destination')}",
    )


def _search_tavily(settings: Settings, query: dict) -> list[dict]:
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(
        query=f"best attractions and local travel tips for {query.get('destination')}",
        max_results=8,
        search_depth="basic",
    )
    return [
        {
            "name": item.get("title", "Attraction research result"),
            "url": item.get("url"),
            "summary": item.get("content", ""),
            "source": "tavily",
        }
        for item in response.get("results", [])
    ]
