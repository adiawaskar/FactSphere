# content_extractor.py
from typing import List
import trafilatura
from googlesearch import search
from config import CONSOLE

def get_google_urls(query: str, num_results: int = 10) -> List[str]:
    """Fetches Google search URLs for a given query."""
    CONSOLE.print(f"\n[yellow]🔍 Searching Google for:[/yellow] '{query}'")
    try:
        return list(search(query, num_results=num_results, lang="en"))
    except Exception as e:
        CONSOLE.print(f"[bold red]Error during Google search: {e}[/bold red]")
        return []

def extract_content_from_url(url: str) -> str | None:
    """Extracts the main text content from a URL using trafilatura."""
    CONSOLE.print(f"--> [cyan]Extracting content from:[/cyan] {url}")
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        CONSOLE.print("[red]    Error: Could not retrieve webpage.[/red]")
        return None
    
    text = trafilatura.extract(
        downloaded, include_comments=False, include_tables=False, no_fallback=True
    )
    if text:
        CONSOLE.print("[green]    --> Successfully extracted content.[/green]")
        return text
    else:
        CONSOLE.print("[red]    Error: Could not extract main content.[/red]")
        return None