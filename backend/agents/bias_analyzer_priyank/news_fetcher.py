# # agents/bias_analyzer_priyank/news_fetcher.py
# from typing import List
# import requests
# from googlesearch import search
# from .config import CONSOLE, GNEWS_API_KEY

# # --- Engine 1: Python Google Search Library ---

# def get_urls_from_google_search(query: str, num_results: int = 10) -> List[str]:
#     """Fetches Google search URLs for a given query using the googlesearch library."""
#     CONSOLE.print(f"\n[yellow]🔍 Searching Google for:[/yellow] '{query}'")
#     try:
#         # The library returns a generator, so we convert it to a list
#         return list(search(query, num_results=num_results, lang="en"))
#     except Exception as e:
#         CONSOLE.print(f"[bold red]Error during Google search: {e}[/bold red]")
#         return []

# # --- Engine 2: GNews.io API ---

# def get_urls_from_gnews(topic: str, max_results: int = 10) -> List[str]:
#     """Fetches news article URLs for a topic using the GNews.io API."""
#     CONSOLE.print(f"\n[yellow]🔍 Searching GNews.io API for:[/yellow] '{topic}'")
#     if not GNEWS_API_KEY:
#         CONSOLE.print("[bold red]GNEWS_API_KEY not found in environment variables.[/bold red]")
#         return []

#     # The GNews API works better with simpler topics rather than complex search queries
#     # We will use the original topic for the API call.
#     url = f"https://gnews.io/api/v4/search?lang=en&max={max_results}&q=\"{topic}\"&token={GNEWS_API_KEY}"
    
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
#         data = response.json()
#         articles = data.get("articles", [])
#         if not articles:
#             CONSOLE.print("[yellow]GNews API returned no articles for this topic.[/yellow]")
#             return []
#         # Extract just the URLs from the article objects
#         return [article['url'] for article in articles]
#     except requests.exceptions.RequestException as e:
#         CONSOLE.print(f"[bold red]Failed to fetch news from GNews API: {e}[/bold red]")
#         return []
#     except KeyError as e:
#         CONSOLE.print(f"[bold red]Unexpected response format from GNews API. Missing key: {e}[/bold red]")
#         return []

# # agents/bias_analyzer_priyank/news_fetcher.py
# from typing import List
# import requests
# from googlesearch import search
# from .config import CONSOLE, GNEWS_API_KEY

# # --- Engine 1: Python Google Search Library ---

# def get_urls_from_google_search(query: str, num_results: int = 10) -> List[str]:
#     """Fetches Google search URLs for a given query using the googlesearch library."""
#     CONSOLE.print(f"\n[yellow]🔍 Searching Google for:[/yellow] '{query}'")
#     try:
#         # The library returns a generator, so we convert it to a list
#         return list(search(query, num_results=num_results, lang="en"))
#     except Exception as e:
#         CONSOLE.print(f"[bold red]Error during Google search: {e}[/bold red]")
#         return []

# # --- Engine 2: GNews.io API ---

# def get_urls_from_gnews(topic: str, max_results: int = 10) -> List[str]:
#     """Fetches news article URLs for a topic using the GNews.io API."""
#     CONSOLE.print(f"\n[yellow]🔍 Searching GNews.io API for:[/yellow] '{topic}'")
#     if not GNEWS_API_KEY:
#         CONSOLE.print("[bold red]GNEWS_API_KEY not found in environment variables.[/bold red]")
#         return []

#     # The GNews API works better with simpler topics rather than complex search queries
#     # We will use the original topic for the API call.
#     url = f"https://gnews.io/api/v4/search?lang=en&max={max_results}&q=\"{topic}\"&token={GNEWS_API_KEY}"
    
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
#         data = response.json()
#         articles = data.get("articles", [])
#         if not articles:
#             CONSOLE.print("[yellow]GNews API returned no articles for this topic.[/yellow]")
#             return []
#         # Extract just the URLs from the article objects
#         return [article['url'] for article in articles]
#     except requests.exceptions.RequestException as e:
#         CONSOLE.print(f"[bold red]Failed to fetch news from GNews API: {e}[/bold red]")
#         return []
#     except KeyError as e:
#         CONSOLE.print(f"[bold red]Unexpected response format from GNews API. Missing key: {e}[/bold red]")
#         return []

# agents/bias_analyzer_priyank/news_fetcher.py
import requests
import time
import re
from typing import List, Optional
from urllib.parse import quote
from .config import CONSOLE, GNEWS_API_KEY, SERPER_API_KEY

def get_urls_from_google_search(query: str, num_results: int = 5) -> List[str]:
    """
    Get URLs from Google search using multiple fallback methods.
    """
    urls = []
    
    # Method 1: Try Serper API if available
    if SERPER_API_KEY:
        try:
            urls = _search_serper_api(query, num_results)
            if urls:
                CONSOLE.print(f"[green]Serper API found {len(urls)} URLs[/green]")
                return urls
        except Exception as e:
            CONSOLE.print(f"[yellow]Serper API failed: {e}[/yellow]")
    
    # Method 2: Try direct Google search (simple approach)
    try:
        urls = _search_google_direct(query, num_results)
        if urls:
            CONSOLE.print(f"[green]Direct search found {len(urls)} URLs[/green]")
            return urls
    except Exception as e:
        CONSOLE.print(f"[yellow]Direct search failed: {e}[/yellow]")
    
    # Method 3: Fallback to DuckDuckGo
    try:
        urls = _search_duckduckgo(query, num_results)
        if urls:
            CONSOLE.print(f"[green]DuckDuckGo found {len(urls)} URLs[/green]")
            return urls
    except Exception as e:
        CONSOLE.print(f"[yellow]DuckDuckGo failed: {e}[/yellow]")
    
    return []

def _search_serper_api(query: str, num_results: int) -> List[str]:
    """Use Serper API for Google search results."""
    if not SERPER_API_KEY:
        return []
        
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": num_results
    }
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    urls = []
    
    # Extract organic results
    if 'organic' in data:
        for result in data['organic']:
            if 'link' in result:
                urls.append(result['link'])
    
    return urls[:num_results]

def _search_google_direct(query: str, num_results: int) -> List[str]:
    """Simple direct Google search fallback."""
    # This is a basic implementation - you might need to adjust based on your environment
    try:
        from googlesearch import search
        urls = list(search(query, num_results=num_results, advanced=False))
        return urls
    except ImportError:
        CONSOLE.print("[yellow]googlesearch-python not installed. Install with: pip install googlesearch-python[/yellow]")
        return []
    except Exception as e:
        CONSOLE.print(f"[yellow]Direct Google search failed: {e}[/yellow]")
        return []

def _search_duckduckgo(query: str, num_results: int) -> List[str]:
    """DuckDuckGo search as fallback."""
    import requests
    from bs4 import BeautifulSoup
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Use DuckDuckGo Lite for simpler parsing
    url = f"https://lite.duckduckgo.com/lite/?q={quote(query)}"
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = []
    
    # DuckDuckGo Lite has result links in specific table cells
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('http') and 'duckduckgo.com' not in href:
            urls.append(href)
        if len(urls) >= num_results:
            break
    
    return urls

def get_urls_from_gnews(query: str, max_results: int = 5) -> List[str]:
    """
    Get URLs from Google News with proper query formatting and error handling.
    """
    if not GNEWS_API_KEY:
        CONSOLE.print("[yellow]GNews API key not configured[/yellow]")
        return []
    
    urls = []
    
    try:
        # GNews API endpoint
        url = "https://gnews.io/api/v4/search"
        
        # Clean and format the query for GNews
        clean_query = _clean_gnews_query(query)
        
        params = {
            'q': clean_query,
            'lang': 'en',
            'max': max_results,
            'token': GNEWS_API_KEY
        }
        
        CONSOLE.print(f"[blue]Searching GNews for: {clean_query}[/blue]")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            error_msg = response.text
            CONSOLE.print(f"[red]GNews API error {response.status_code}: {error_msg}[/red]")
            
            # Try with a simpler query if complex query fails
            if "syntax error" in error_msg:
                simple_query = _simplify_query(query)
                if simple_query != clean_query:
                    CONSOLE.print(f"[yellow]Trying simplified query: {simple_query}[/yellow]")
                    return get_urls_from_gnews(simple_query, max_results)
            return []
        
        data = response.json()
        
        if 'articles' not in data or not data['articles']:
            CONSOLE.print("[yellow]No articles found in GNews response[/yellow]")
            return []
        
        for article in data['articles']:
            if 'url' in article and article['url']:
                urls.append(article['url'])
        
        CONSOLE.print(f"[green]GNews found {len(urls)} articles[/green]")
        return urls
        
    except requests.exceptions.Timeout:
        CONSOLE.print("[red]GNews API timeout[/red]")
        return []
    except requests.exceptions.RequestException as e:
        CONSOLE.print(f"[red]GNews API request failed: {e}[/red]")
        return []
    except Exception as e:
        CONSOLE.print(f"[red]Unexpected error with GNews: {e}[/red]")
        return []

def _clean_gnews_query(query: str) -> str:
    """
    Clean and format query for GNews API syntax requirements.
    GNews has specific syntax rules for queries.
    """
    # Remove special characters that might cause syntax errors
    clean_query = re.sub(r'[^\w\s\-]', ' ', query)
    
    # Remove extra whitespace
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()
    
    # Limit query length
    if len(clean_query) > 100:
        clean_query = clean_query[:100]
    
    return clean_query

def _simplify_query(query: str) -> str:
    """
    Simplify complex queries for GNews by taking key terms.
    """
    # Remove common problematic phrases
    simple_query = query
    
    # Take first few words if query is too complex
    words = query.split()
    if len(words) > 5:
        simple_query = ' '.join(words[:4])
    
    return simple_query.strip()

# Enhanced search function for the fact-checking system
def enhanced_web_search(query: str, search_type: str = "general", num_results: int = 5) -> List[str]:
    """
    Enhanced search that handles different types of queries.
    
    Args:
        query: Search query
        search_type: "general", "news", or "factcheck"
        num_results: Number of results to return
    """
    urls = []
    
    if search_type == "news":
        # Prefer GNews for news searches
        urls = get_urls_from_gnews(query, num_results)
        if not urls:
            urls = get_urls_from_google_search(query, num_results)
    
    elif search_type == "factcheck":
        # Add fact-check specific sites to query
        factcheck_query = f"{query} site:snopes.com OR site:politifact.com OR site:factcheck.org OR site:reuters.com"
        urls = get_urls_from_google_search(factcheck_query, num_results)
        if not urls:
            urls = get_urls_from_google_search(query, num_results)
    
    else:  # general search
        # Try multiple sources
        urls = get_urls_from_google_search(query, num_results)
        if not urls:
            urls = get_urls_from_gnews(query, num_results)
    
    return urls

# Alternative simple search function
def simple_web_search(query: str, num_results: int = 5) -> List[str]:
    """
    Simple reliable search using multiple fallbacks.
    """
    # Try multiple search methods
    methods = [
        lambda: get_urls_from_google_search(query, num_results),
        lambda: get_urls_from_gnews(query, num_results),
    ]
    
    for method in methods:
        try:
            urls = method()
            if urls:
                return urls
        except Exception as e:
            CONSOLE.print(f"[yellow]Search method failed: {e}[/yellow]")
            continue
    
    CONSOLE.print("[red]All search methods failed[/red]")
    return []