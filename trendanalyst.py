from google.adk.agents import LlmAgent

def scrape_trends(category: str) -> str:
    """
    Simulates scraping web or social signals for visual styles.
    """
    # Placeholder for trend scraping logic
    trends = {
        "electronics": "minimalist pastel, high-tech gloss",
        "fashion": "retro vintage, grain filter",
        "home": "warm wooden, cozy lighting"
    }
    return trends.get(category.lower(), "modern clean")

def get_trend_analyst():
    return LlmAgent(
        name="TrendAnalyst",
        model="gemini-2.5-flash",
        instruction="You are a Trend Analyst (Agent A). Scrape web/social signals to identify converting visual styles.",
        tools=[scrape_trends]
    )
