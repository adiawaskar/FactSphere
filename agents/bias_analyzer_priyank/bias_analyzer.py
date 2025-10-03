# agents/bias_analyzer_priyank/bias_analyzer.py

import sys
import json
import logging
from typing import Dict, List, Any, Tuple

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from rich.table import Table

# Use the central configuration from the project
from config import CONSOLE, GEMINI_API_KEY, LLM_FAST_MODEL

# Configure logging for the module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BiasAnalysisAgent:
    """
    An AI agent that analyzes news articles for bias using an LLM
    based on a predefined 13-point framework.
    """
    def __init__(self, content: str, source_url: str = "Unknown Source"):
        """
        Initializes the agent with the article content and its source URL.
        """
        # API key check is now centralized in main.py
        self.content = content
        self.source_url = source_url
        self.model = genai.GenerativeModel(LLM_FAST_MODEL)
        
        # --- SINGLE SOURCE OF TRUTH ---
        # This dictionary now defines the exact category names and their weights.
        # The prompt will be generated directly from these keys.
        self.weights = {
            'Title Analysis': 5,
            'Authorship': 5,
            'Word Choice & Tone': 15,
            'Framing & Context': 10,
            'Sources & Attribution': 15,
            'Omission & Agenda': 10,
            'Placement & Visuals': 5,
            'Labeling': 5,
            'Moral & Value Appeals': 10,
            'Sentiment Toward Political Actors': 10,
            'Narrative Construction': 5,
            'Fact vs Opinion': 10,
            'Confirmation Bias': 5
        }

    def _generate_prompt(self) -> str:
        """
        Generates a highly specific prompt, instructing the LLM to use the exact
        category names defined in the self.weights dictionary.
        """
        # Dynamically create the list of categories from our single source of truth.
        category_list_str = "\n".join([f"- `{name}`" for name in self.weights.keys()])

        return f"""
        You are a meticulous and impartial media bias analyst. Your task is to analyze the provided news article based on a strict 13-point framework.

        **Instructions:**
        Your entire output **MUST** be a single, valid JSON object. This object must contain one key, "analysis_results", which is a list of 13 JSON objects.
        
        Each object in the list must have exactly three keys:
        1. `category_name`: A string that **MUST** be one of the exact names from the list below.
        2. `score`: An integer from -5 (strong left bias) to +5 (strong right bias).
        3. `justification`: A concise 1-2 sentence explanation for the score.

        **You MUST use these exact category names:**
        {category_list_str}

        **Article to Analyze (first 8000 characters):**
        ---
        {self.content[:8000]}
        ---
        """

    def _call_llm(self, prompt: str) -> str | None:
        """Calls the Gemini API and handles potential errors gracefully."""
        try:
            # Configure the model generation settings for Gemini
            generation_config = genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            )
            # Generate content using the Gemini model
            completion = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return completion.text
        except (google_exceptions.GoogleAPICallError, ValueError) as e:
            logging.error(f"Gemini API Error for {self.source_url}: {e}")
            CONSOLE.print(f"[bold red]    API Error during analysis. Skipping article.[/bold red]")
            return None

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]] | None:
        """Parses and validates the JSON string from the LLM."""
        try:
            data = json.loads(response_text)
            if "analysis_results" in data and isinstance(data["analysis_results"], list):
                return data["analysis_results"]
            logging.error(f"LLM response for {self.source_url} had invalid structure.")
            return None
        except json.JSONDecodeError:
            logging.error(f"Failed to decode LLM JSON for {self.source_url}.")
            CONSOLE.print("[bold red]    Error: LLM returned invalid JSON. Skipping article.[/bold red]")
            return None

    def _calculate_bias_score(self, analysis_data: List[Dict[str, Any]]) -> float:
        """Calculates the final weighted bias index from the analysis data."""
        total_weighted_score = 0.0
        for item in analysis_data:
            category = item.get("category_name")
            score = item.get("score")
            # This check will now work correctly for all categories.
            if category in self.weights and isinstance(score, (int, float)):
                normalized_score = score / 5.0
                weight_percentage = self.weights[category] / 100.0
                total_weighted_score += normalized_score * weight_percentage
            else:
                logging.warning(f"Skipping invalid category/score for {self.source_url}: {item}")
        return total_weighted_score

    def _interpret_final_score(self, score: float) -> str:
        """Interprets the final score into a human-readable judgment."""
        if -1.0 <= score < -0.6: return "Strong Left Bias"
        if -0.6 <= score < -0.3: return "Moderate Left Bias"
        if -0.3 <= score < -0.1: return "Slight Left Bias"
        if -0.1 <= score <= 0.1: return "Neutral / Balanced"
        if 0.1 < score <= 0.3:  return "Slight Right Bias"
        if 0.3 < score <= 0.6:  return "Moderate Right Bias"
        if 0.6 < score <= 1.0:  return "Strong Right Bias"
        return "Indeterminate Score"

    def _display_results(self, analysis_data: List[Dict[str, Any]], final_score: float, judgment: str):
        """Displays the full analysis in a formatted table."""
        table = Table(
            title=f"[bold cyan]Bias Analysis Report for:[/] [dim]{self.source_url}[/dim]",
            show_header=True, header_style="bold magenta"
        )
        table.add_column("Category", style="dim", width=30)
        table.add_column("Weight", justify="center")
        table.add_column("Score (-5 to +5)", justify="center")
        table.add_column("Justification", style="italic")

        for item in analysis_data:
            score = item.get('score', 0)
            category_name = item.get('category_name', 'N/A')
            score_color = "red" if score < 0 else "blue" if score > 0 else "white"
            
            # This lookup will now work correctly.
            weight = self.weights.get(category_name, 0)

            table.add_row(
                category_name,
                f"{weight}%",
                f"[{score_color}]{score}[/{score_color}]",
                item.get('justification', 'No justification provided.')
            )

        CONSOLE.print(table)
        CONSOLE.print("\n--- [bold]Final Judgment[/bold] ---")
        CONSOLE.print(f"Final Bias Index: [bold]{final_score:.3f}[/bold]")
        CONSOLE.print(f"Overall Assessment: [bold]{judgment}[/bold]\n")

    def run(self) -> Tuple[float, str] | None:
        """Orchestrates the analysis and returns the results for main.py."""
        if not self.content or not self.content.strip():
            logging.warning(f"Content for {self.source_url} is empty. Skipping.")
            return None

        CONSOLE.print(f"[yellow]    Analyzing for bias: {self.source_url}...[/yellow]")
        prompt = self._generate_prompt()
        llm_response_str = self._call_llm(prompt)
        if not llm_response_str:
            return None

        analysis_data = self._parse_llm_response(llm_response_str)
        if not analysis_data:
            return None

        final_score = self._calculate_bias_score(analysis_data)
        judgment = self._interpret_final_score(final_score)
        
        self._display_results(analysis_data, final_score, judgment)

        return final_score, judgment