# agents/timeline/05_narrative_generator.py
import json
import google.generativeai as genai
from typing import List, Dict
from config import CONSOLE, LLM_SMART_MODEL

def generate_narrative(sorted_events: List[Dict]) -> Dict:
    """
    Uses the Gemini model to generate background, timeline, and conclusion.
    """
    model = genai.GenerativeModel(LLM_SMART_MODEL)
    
    # Format the events into a string for the prompt
    event_list_str = "\n".join(
        [f"- {event['date']}: {event['title']} - {event['description']}" for event in sorted_events]
    )

    prompt = f"""
    You are a historian and news analyst. Based on the following chronological list of events,
    generate a coherent and accurate narrative. The output MUST be a single JSON object with three keys:
    "background", "timeline", and "conclusion".

    - "background": A summary of the underlying causes and context leading up to the first event.
    - "timeline": A list of objects, where each object has "date", "event" (title), and "details" (description).
    - "conclusion": A summary of the outcome and current situation based on the final events.

    CHRONOLOGICAL EVENTS:
    ---
    {event_list_str}
    ---

    JSON OUTPUT:
    """

    try:
        CONSOLE.print("\n[yellow]✍️ Generating final narrative with LLM...[/yellow]")
        generation_config = genai.types.GenerationConfig(
            temperature=0.5,
            response_mime_type="application/json",
        )
        response = model.generate_content(prompt, generation_config=generation_config)
        narrative = json.loads(response.text)
        CONSOLE.print("[green]   --> Narrative generation complete.[/green]")
        return narrative

    except (Exception) as e:
        CONSOLE.print(f"[bold red]LLM Narrative Generation Error: {e}[/bold red]")
        return {
            "background": "Error generating background.",
            "timeline": [],
            "conclusion": "Error generating conclusion."
        }