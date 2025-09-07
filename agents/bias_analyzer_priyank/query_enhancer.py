# query_enhancer.py
import json
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from config import CONSOLE, LLM_FAST_MODEL

def enhance_query(topic: str) -> str:
    """
    Uses a Gemini LLM to convert a user topic into a refined Google search query.
    """
    CONSOLE.print(f"\n[yellow]✨ Enhancing search query for:[/yellow] '{topic}'")
    
    # API key check is now centralized in main.py
    model = genai.GenerativeModel(LLM_FAST_MODEL)
    
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
        generation_config = genai.types.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
        )
        completion = model.generate_content(prompt, generation_config=generation_config)
        response = json.loads(completion.text)
        enhanced_query = response.get("search_query", topic)
        
        # Add Google search operators to refine results
        final_query = f'"{enhanced_query}" -site:wikipedia.org -site:youtube.com'
        
        CONSOLE.print(f"[green]   --> Generated Query:[/green] {final_query}")
        return final_query

    except (google_exceptions.GoogleAPICallError, json.JSONDecodeError, ValueError) as e:
        CONSOLE.print(f"[bold red]Could not enhance query via LLM: {e}. Using basic query.[/bold red]")
        return f'"{topic}" news -site:wikipedia.org'