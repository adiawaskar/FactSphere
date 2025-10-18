# # agents/timeline/o1_retrieval.py
# import requests
# import trafilatura
# from typing import List, Dict, Optional
# from .config import GNEWS_API_KEY, CONSOLE
# import dateparser
# # --- Add this import for URL encoding ---
# from urllib.parse import quote

# def get_urls_from_gnews(topic: str, max_results: int = 10) -> List[Dict[str, str]]:
#     """Fetches news articles (URL and published date) from the GNews.io API."""
#     CONSOLE.print(f"\n[yellow]🔍 Searching GNews.io for:[/yellow] '{topic}'")
#     if not GNEWS_API_KEY:
#         CONSOLE.print("[bold red]GNEWS_API_KEY not found.[/bold red]")
#         return []

#     # --- CHANGE THIS SECTION ---
#     # 1. URL encode the topic to handle spaces and special characters safely.
#     encoded_topic = quote(topic)

#     # 2. Remove the extra quotes \" around the topic in the URL.
#     url = f"https://gnews.io/api/v4/search?lang=en&max={max_results}&q={encoded_topic}&token={GNEWS_API_KEY}"
#     # --- END CHANGE ---
    
#     # For debugging, let's print the exact URL we are calling
#     CONSOLE.print(f"[grey50]   --> Request URL: {url}[/grey50]")

#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         data = response.json()
#         articles = data.get("articles", [])
#         if not articles:
#             CONSOLE.print("[yellow]GNews API returned no articles. Check the query or API key.[/yellow]")
#             # Also print the raw response to see if there's an error message from the API
#             CONSOLE.print(f"[grey50]   --> Raw Response: {response.text}[/grey50]")
#             return []
            
#         return [{"url": article['url'], "published_at": article['publishedAt']} for article in articles]
#     except requests.exceptions.RequestException as e:
#         CONSOLE.print(f"[bold red]Failed to fetch news from GNews API: {e}[/bold red]")
#         return []

# def extract_content_from_url(url: str, published_at: str) -> Optional[Dict]:
#     """Extracts main content and metadata from a URL."""
#     CONSOLE.print(f"--> [cyan]Extracting content from:[/cyan] {url}")
#     downloaded = trafilatura.fetch_url(url)
#     if downloaded is None:
#         CONSOLE.print("[red]    Error: Could not retrieve webpage.[/red]")
#         return None

#     content = trafilatura.extract(
#         downloaded, include_comments=False, include_tables=False, no_fallback=True
#     )

#     if content:
#         parsed_date = dateparser.parse(published_at)
#         formatted_date = parsed_date.strftime('%Y-%m-%d') if parsed_date else None
        
#         metadata = {
#             "url": url,
#             "title": trafilatura.extract_metadata(downloaded).title,
#             "published_date": formatted_date,
#             "source": trafilatura.extract_metadata(downloaded).sitename,
#             "content": content
#         }
#         CONSOLE.print("[green]    --> Successfully extracted content and metadata.[/green]")
#         return metadata
#     else:
#         CONSOLE.print("[red]    Error: Could not extract main content.[/red]")
#         return None

# agents/timeline/o1_retrieval.py
import requests
import trafilatura
from typing import List, Dict, Optional
from .config import GNEWS_API_KEY, CONSOLE
import dateparser
from urllib.parse import quote

def get_urls_from_gnews(topic: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Fetches news articles (URL and published date) from the GNews.io API."""
    CONSOLE.print(f"\n[yellow]🔍 Searching GNews.io for:[/yellow] '{topic}'")
    if not GNEWS_API_KEY:
        CONSOLE.print("[bold red]GNEWS_API_KEY not found.[/bold red]")
        return []

    # --- CORRECTED SECTION ---
    # 1. Wrap the topic in double quotes for multi-word queries, as required by the GNews API.
    quoted_topic = f'"{topic}"'
    
    # 2. Now, URL-encode the entire quoted string to handle spaces and special characters.
    encoded_topic = quote(quoted_topic)

    url = f"https://gnews.io/api/v4/search?lang=en&max={max_results}&q={encoded_topic}&token={GNEWS_API_KEY}"
    # --- END CORRECTED SECTION ---
    
    # For debugging, let's print the exact URL we are calling
    CONSOLE.print(f"[grey50]   --> Request URL: {url}[/grey50]")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            CONSOLE.print("[yellow]GNews API returned no articles. Check the query or API key.[/yellow]")
            CONSOLE.print(f"[grey50]   --> Raw Response: {response.text}[/grey50]")
            return []
            
        return [{"url": article['url'], "published_at": article['publishedAt']} for article in articles]
    except requests.exceptions.RequestException as e:
        CONSOLE.print(f"[bold red]Failed to fetch news from GNews API: {e}[/bold red]")
        return []

def extract_content_from_url(url: str, published_at: str) -> Optional[Dict]:
    """Extracts main content and metadata from a URL."""
    CONSOLE.print(f"--> [cyan]Extracting content from:[/cyan] {url}")
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        CONSOLE.print("[red]    Error: Could not retrieve webpage.[/red]")
        return None

    content = trafilatura.extract(
        downloaded, include_comments=False, include_tables=False, no_fallback=True
    )

    if content:
        parsed_date = dateparser.parse(published_at)
        formatted_date = parsed_date.strftime('%Y-%m-%d') if parsed_date else None
        
        metadata = {
            "url": url,
            "title": trafilatura.extract_metadata(downloaded).title,
            "published_date": formatted_date,
            "source": trafilatura.extract_metadata(downloaded).sitename,
            "content": content
        }
        CONSOLE.print("[green]    --> Successfully extracted content and metadata.[/green]")
        return metadata
    else:
        CONSOLE.print("[red]    Error: Could not extract main content.[/red]")
        return None