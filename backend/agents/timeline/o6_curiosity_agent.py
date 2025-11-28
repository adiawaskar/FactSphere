# agents/timeline/o6_curiosity_agent.py
import json
import google.generativeai as genai
from typing import List, Dict
from .config import CONSOLE, LLM_SMART_MODEL, GEMINI_API_KEY
from .o4_graph_builder import Neo4jGraph

# Ensure robust connection
genai.configure(api_key=GEMINI_API_KEY, transport="rest")

def generate_curiosity_queries(graph_instance: Neo4jGraph, current_iteration: int) -> List[str]:
    """
    Analyzes the current graph state to generate deep-dive queries.
    """
    CONSOLE.print(f"\n[bold magenta]🤔 Curiosity Agent is thinking (Iteration {current_iteration})...[/bold magenta]")
    
    # 1. Get a summary of the current knowledge from Neo4j
    # We fetch the last 15 events to give context to the LLM
    events = graph_instance.get_sorted_events()
    
    if not events:
        return []

    # Summarize context for the LLM
    context_summary = "\n".join(
        [f"- {e['date']}: {e['title']}" for e in events[-20:]] # Pass last 20 events max
    )
    
    prompt = f"""
    You are a Senior Investigative Journalist Agent. 
    You are currently building a timeline of events.
    
    CURRENT KNOWN EVENTS (Chronological):
    ---
    {context_summary}
    ---

    YOUR TASK:
    Analyze the gaps in the story above. Be curious. 
    1. Are there key "Actors" (people/orgs) mentioned who need background checks?
    2. Are there specific laws, reports, or research mentioned that we should search for directly?
    3. Is the "beginning" missing? (Do we need to search for history before the first date?)
    4. Is the "conclusion" missing? (Do we need updates on recent court dates etc?)

    OUTPUT:
    Generate a JSON list of 2 to 3 specific DuckDuckGo search strings.
    Each query must be distinct and aimed at uncovering NEW information.
    Use syntax like "history of..." or "who is [Person]" or "details of [Law]".
    
    JSON FORMAT:
    ["query 1", "query 2", "query 3"]
    """

    try:
        model = genai.GenerativeModel(LLM_SMART_MODEL)
        response = model.generate_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
        )
        
        queries = json.loads(response.text)
        CONSOLE.print(f"[cyan]   --> Generated follow-up queries:[/cyan]")
        for q in queries:
            CONSOLE.print(f"       - {q}")
            
        return queries

    except Exception as e:
        CONSOLE.print(f"[red]Curiosity generation failed: {e}[/red]")
        return []