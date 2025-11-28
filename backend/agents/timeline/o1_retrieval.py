# agents/timeline/o1_retrieval.py
import trafilatura
from typing import List, Dict, Optional
from .config import CONSOLE
import dateparser
from duckduckgo_search import DDGS

def get_urls_from_duckduckgo(topic: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Fetches news articles from DuckDuckGo."""
    CONSOLE.print(f"\n[yellow]🔍 Searching DuckDuckGo for:[/yellow] '{topic}'")
    
    results = []
    try:
        # DDGS provides a simple interface to search
        with DDGS() as ddgs:
            # We use ddgs.news() specifically for news articles
            # region='wt-wt' searches globally (no specific region)
            ddg_news = ddgs.news(keywords=topic, max_results=max_results)
            
            if not ddg_news:
                CONSOLE.print("[yellow]DuckDuckGo returned no results.[/yellow]")
                return []

            # Normalize data to match the format expected by main.py
            for result in ddg_news:
                results.append({
                    "url": result['url'],
                    # DDG returns 'date' (e.g., "2024-01-01T..."), we map it to 'published_at'
                    "published_at": result.get('date', '') 
                })
                
        CONSOLE.print(f"[green]   --> Found {len(results)} articles.[/green]")
        return results

    except Exception as e:
        CONSOLE.print(f"[bold red]Failed to fetch news from DuckDuckGo: {e}[/bold red]")
        return []

def extract_content_from_url(url: str, published_at: str) -> Optional[Dict]:
    """Extracts main content and metadata from a URL."""
    CONSOLE.print(f"--> [cyan]Extracting content from:[/cyan] {url}")
    
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            CONSOLE.print("[red]    Error: Could not retrieve webpage.[/red]")
            return None

        content = trafilatura.extract(
            downloaded, include_comments=False, include_tables=False, no_fallback=True
        )

        if content:
            # Parse the date provided by DDG or try to find it in metadata
            parsed_date = dateparser.parse(published_at) if published_at else None
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
    except Exception as e:
         CONSOLE.print(f"[red]    Error during extraction: {e}[/red]")
         return None