# query_enhancer.py
import json
from groq import Groq, APIError
from config import CONSOLE, GROQ_API_KEY, LLM_FAST_MODEL

def enhance_query(topic: str) -> str:
    """
    Uses an LLM to convert a user topic into a refined Google search query,
    focusing on news and excluding specific sites.
    """
    CONSOLE.print(f"\n[yellow]✨ Enhancing search query for:[/yellow] '{topic}'")
    
    if not GROQ_API_KEY:
        CONSOLE.print("[bold red]GROQ_API_KEY not found. Skipping query enhancement.[/bold red]")
        return f'"{topic}" news'

    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
    You are a search engine expert. Your task is to convert a user's topic into an effective Google search query.
    The query should be neutral, specific, and aimed at finding high-quality news articles.

    User Topic: "{topic}"

    Instructions:
    1.  Rephrase the topic into a neutral, fact-finding search query.
    2.  Identify 2-3 essential keywords from the topic.
    3.  Your output MUST be a single JSON object with two keys: "search_query" and "keywords".

    Example:
    User Topic: "government spying on citizens"
    JSON Output: {{"search_query": "government surveillance programs and civil liberties news", "keywords": ["surveillance", "privacy", "policy"]}}
    """
    
    try:
        completion = client.chat.completions.create(
            model=LLM_FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        response = json.loads(completion.choices[0].message.content)
        enhanced_query = response.get("search_query", topic)
        
        # Add Google search operators to refine results
        final_query = f'"{enhanced_query}" -site:wikipedia.org -site:youtube.com'
        
        CONSOLE.print(f"[green]   --> Generated Query:[/green] {final_query}")
        return final_query

    except (APIError, json.JSONDecodeError) as e:
        CONSOLE.print(f"[bold red]Could not enhance query via LLM: {e}. Using basic query.[/bold red]")
        return f'"{topic}" news -site:wikipedia.org'