# agents/timeline/03_event_extraction.py
import json
import google.generativeai as genai
from typing import List, Dict, Optional
from .config import CONSOLE, LLM_SMART_MODEL, GEMINI_API_KEY
import time

# Configure the Gemini API client
genai.configure(api_key=GEMINI_API_KEY, transport="rest")

def extract_events_from_chunk(chunk: Dict) -> Optional[List[Dict]]:
    """
    Uses Gemini to extract structured events from a text chunk.
    """
    model = genai.GenerativeModel(LLM_SMART_MODEL)
    
    prompt = f"""
    You are an expert data analyst. From the following text chunk, extract key factual events.
    For each event, provide a short title, a concise description, the explicit date if mentioned,
    a list of actors (people, organizations, countries), and the location.
    The output MUST be a valid JSON list of objects. Each object should have the keys:
    "event_title", "description", "explicit_date", "actors", "location".
    If no specific events are found, return an empty list [].

    TEXT CHUNK:
    ---
    {chunk['text']}
    ---
    
    JSON OUTPUT:
    """

    try:
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        )
        response = model.generate_content(prompt, generation_config=generation_config)
        time.sleep(2) # Wait for 2 seconds to stay within free tier limits
        extracted_data = json.loads(response.text)
        
        # Add source URL and inferred date to each event
        for event in extracted_data:
            event['source_url'] = chunk['metadata'].get('source_url')
            event['inferred_date'] = chunk['metadata'].get('pub_date') # Use article pub_date for context

        return extracted_data

    except (Exception) as e:
        CONSOLE.print(f"[bold red]LLM Event Extraction Error: {e}[/bold red]")
        time.sleep(5) # Wait longer after an error
        return None