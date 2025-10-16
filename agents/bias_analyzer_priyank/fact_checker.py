# agents/bias_analyzer_priyank/fact_checker.py
import json
from typing import List
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from .config import CONSOLE, LLM_FAST_MODEL, LLM_SMART_MODEL

def generate_misconceptions(biased_content: str) -> List[str]:
    """Uses an LLM to generate leading questions from biased content."""
    CONSOLE.print("[yellow]    Generating misconceptions from biased content...[/yellow]")
    model = genai.GenerativeModel(LLM_FAST_MODEL)
    prompt = f"""
    You are a naive reader who trusts everything and reacts emotionally.
    After reading the following biased article, generate 2-3 leading questions or common misconceptions
    that someone might form. Output MUST be a JSON object with a key "misconceptions" containing a list of strings.

    Article:
    ---
    {biased_content[:4000]}
    ---
    """
    try:
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            response_mime_type="application/json",
        )
        completion = model.generate_content(prompt, generation_config=generation_config)
        response = json.loads(completion.text)
        misconceptions = response.get("misconceptions", [])
        for q in misconceptions:
            CONSOLE.print(f"    --> [magenta]Generated Question:[/magenta] {q}")
        return misconceptions
    except (google_exceptions.GoogleAPICallError, json.JSONDecodeError, KeyError, ValueError) as e:
        CONSOLE.print(f"[bold red]Error generating misconceptions: {e}[/bold red]")
        return []

def generate_fact_check_report(misconception: str, neutral_chunks: List[str], source_url: str):
    """Generates a fact-check report using retrieved neutral evidence."""
    CONSOLE.print(f"\n[cyan]Generating Fact-Check Report for:[/cyan] '{misconception}'")
    if not neutral_chunks:
        CONSOLE.print("[yellow]Warning: No neutral reporting available to fact-check this claim.[/yellow]")
        return

    model = genai.GenerativeModel(LLM_SMART_MODEL)
    context = "\n\n---\n\n".join(neutral_chunks)
    prompt = f"""
    You are a fact-checker. Use the "Neutral Evidence" to address the "Misconception Question".

    Misconception Question: "{misconception}"
    Biased Source: {source_url}

    Neutral Evidence:
    ---
    {context}
    ---

    Your task is to generate a report as a single JSON object with three keys:
    1.  "correction": A clear, neutral paragraph correcting the misconception, adding nuance and missing facts.
    2.  "confidence_score": "High", "Medium", or "Low", based on how well the evidence addresses the question.
    3.  "balanced_summary": A summary acknowledging complexity but stating what sources confirm.
    """
    try:
        generation_config = genai.types.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
        )
        completion = model.generate_content(prompt, generation_config=generation_config)
        report = json.loads(completion.text)

        # Display User-Facing Output
        CONSOLE.print("\n" + "="*50)
        CONSOLE.print("[bold underline]Fact-Check Report[/bold underline]\n")
        CONSOLE.print(f"[bold red]Misconception:[/bold red] {misconception}")
        CONSOLE.print(f"([italic]From biased source: {source_url}[/italic])\n")
        CONSOLE.print(f"[bold green]Correction:[/bold green] {report.get('correction', 'N/A')}\n")
        CONSOLE.print(f"[bold]Confidence:[/bold] {report.get('confidence_score', 'N/A')}")
        CONSOLE.print(f"[bold]Balanced Summary:[/bold] {report.get('balanced_summary', 'N/A')}\n")
        CONSOLE.print("[bold blue]Evidence Source:[/bold blue] Neutral Knowledge Base")
        CONSOLE.print("="*50 + "\n")
        return report
    except (google_exceptions.GoogleAPICallError, json.JSONDecodeError, KeyError, ValueError) as e:
        CONSOLE.print(f"[bold red]Error generating fact-check report: {e}[/bold red]")
        return None