# agents/bias_analyzer_priyank/content_extractor.py
import trafilatura
from config import CONSOLE

# The get_google_urls function has been removed from this file.

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