# agents/bias_analyzer_priyank/news_fetcher.py
from typing import List
import requests
from googlesearch import search
from config import CONSOLE, GNEWS_API_KEY

# --- Engine 1: Python Google Search Library ---

def get_urls_from_google_search(query: str, num_results: int = 10) -> List[str]:
    """Fetches Google search URLs for a given query using the googlesearch library."""
    CONSOLE.print(f"\n[yellow]🔍 Searching Google for:[/yellow] '{query}'")
    try:
        # The library returns a generator, so we convert it to a list
        return list(search(query, num_results=num_results, lang="en"))
    except Exception as e:
        CONSOLE.print(f"[bold red]Error during Google search: {e}[/bold red]")
        return []

# --- Engine 2: GNews.io API ---

def get_urls_from_gnews(topic: str, max_results: int = 10) -> List[str]:
    """Fetches news article URLs for a topic using the GNews.io API."""
    CONSOLE.print(f"\n[yellow]🔍 Searching GNews.io API for:[/yellow] '{topic}'")
    if not GNEWS_API_KEY:
        CONSOLE.print("[bold red]GNEWS_API_KEY not found in environment variables.[/bold red]")
        return []

    # The GNews API works better with simpler topics rather than complex search queries
    # We will use the original topic for the API call.
    url = f"https://gnews.io/api/v4/search?lang=en&max={max_results}&q=\"{topic}\"&token={GNEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            CONSOLE.print("[yellow]GNews API returned no articles for this topic.[/yellow]")
            return []
        # Extract just the URLs from the article objects
        return [article['url'] for article in articles]
    except requests.exceptions.RequestException as e:
        CONSOLE.print(f"[bold red]Failed to fetch news from GNews API: {e}[/bold red]")
        return []
    except KeyError as e:
        CONSOLE.print(f"[bold red]Unexpected response format from GNews API. Missing key: {e}[/bold red]")
        return []