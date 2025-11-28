# agents/timeline/o0_query_refiner.py
import google.generativeai as genai
from .config import CONSOLE, LLM_SMART_MODEL, GEMINI_API_KEY

# Ensure robust connection
genai.configure(api_key=GEMINI_API_KEY, transport="rest")

def refine_initial_query(topic: str) -> str:
    """
    Refines a raw user topic into a specific DuckDuckGo search query.
    """
    CONSOLE.print(f"\n[yellow]🧠 Refining topic:[/yellow] '{topic}'")
    model = genai.GenerativeModel(LLM_SMART_MODEL)
    
    prompt = f"""
    You are a Search Engine Optimization expert for investigative journalism.
    Convert the user's topic into a precise DuckDuckGo search query.
    
    RULES:
    1. Use advanced operators like quoted phrases "..." for specific entities.
    2. Exclude generic video or encyclopedia sites using -site:youtube.com -site:wikipedia.org.
    3. Focus on news, reports, and timeline-related keywords.
    4. RETURN ONLY THE QUERY STRING. No quotes, no markdown.

    User Topic: {topic}
    """

    try:
        response = model.generate_content(prompt)
        # basic cleaning to ensure we just get the query text
        refined_query = response.text.strip().strip('"').strip("'")
        
        CONSOLE.print(f"[green]   --> Refined Query:[/green] {refined_query}")
        return refined_query
    except Exception as e:
        CONSOLE.print(f"[red]Query refinement failed, using original.[/red]")
        return topic