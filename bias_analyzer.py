# bias_analyzer.py
import sys
import json
import logging
from typing import Dict, List, Any, Tuple

from groq import Groq, APIError
from rich.table import Table

from config import CONSOLE, GROQ_API_KEY, LLM_FAST_MODEL

class BiasAnalysisAgent:
    """Analyzes news articles for bias using an LLM and displays a detailed report."""
    def __init__(self, content: str, source_url: str = "Unknown Source"):
        if not GROQ_API_KEY:
            CONSOLE.print("[bold red]Error: GROQ_API_KEY environment variable not set.[/bold red]")
            sys.exit(1)
        self.content = content
        self.source_url = source_url # For display in the report title
        self.client = Groq(api_key=GROQ_API_KEY)
        self.weights = {
            'Title Analysis': 5, 'Authorship': 5, 'Word Choice & Tone': 15,
            'Framing & Context': 10, 'Sources & Attribution': 15,
            'Omission & Agenda': 10, 'Placement & Visuals': 5, 'Labeling': 5,
            'Moral & Value Appeals': 10, 'Sentiment Toward Political Actors': 10,
            'Narrative Construction': 5, 'Fact vs Opinion': 10, 'Confirmation Bias': 5
        }

    def _generate_prompt(self) -> str:
        # This method is unchanged
        framework_details = """
        1.  **Title Analysis**: Is it neutral or judgmental?
        2.  **Authorship**: Is the author named and credible?
        3.  **Word Choice & Tone**: Are words loaded/emotive or neutral?
        4.  **Framing & Context**: How is the event framed (e.g., riot vs. protest)? Is context selective?
        5.  **Sources & Attribution**: Are sources balanced and credible? Are quotes attributed?
        6.  **Omission & Agenda Setting**: Are important facts or perspectives missing?
        7.  **Placement & Visuals**: Is story placement prominent or buried? (Analyze based on text structure).
        8.  **Labeling**: Are ideological labels used (e.g., "far-right," "radical left")?
        9.  **Moral & Value Appeals**: Does it appeal to left-leaning (fairness, equality) or right-leaning (tradition, patriotism) values?
        10. **Sentiment Toward Political Actors**: Is sentiment positive, negative, or neutral toward parties/leaders?
        11. **Narrative Construction**: Is it a one-sided "heroes vs. villains" story?
        12. **Fact vs. Opinion**: Is the article based on verifiable facts or speculation/commentary?
        13. **Confirmation Bias Check**: Does it only reinforce one worldview without acknowledging complexities?
        """
        return f"""
        You are a meticulous and impartial media bias analyst. Your task is to analyze the provided news article based on a strict 13-point framework.
        **Instructions:**
        For each of the 13 categories, provide a `score` from -5 (strong left) to +5 (strong right) and a concise `justification`.
        Your entire output **MUST** be a single, valid JSON object with a list named "analysis_results".
        **Article to Analyze:**
        ---
        {self.content[:8000]}
        ---
        """

    def _call_llm(self, prompt: str) -> str | None:
        # This method is unchanged
        try:
            completion = self.client.chat.completions.create(
                model=LLM_FAST_MODEL, messages=[{"role": "user", "content": prompt}],
                temperature=0.1, response_format={"type": "json_object"},
            )
            return completion.choices[0].message.content
        except APIError as e:
            CONSOLE.print(f"[bold red]An error occurred with the Groq API: {e}[/bold red]")
            return None

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]] | None:
        # This method is unchanged
        try:
            data = json.loads(response_text)
            if "analysis_results" in data and isinstance(data["analysis_results"], list):
                return data["analysis_results"]
            logging.error("LLM response did not contain 'analysis_results' list.")
            return None
        except json.JSONDecodeError:
            logging.error(f"Failed to decode LLM response into JSON. Response:\n{response_text}")
            return None

    def _calculate_bias_score(self, analysis_data: List[Dict[str, Any]]) -> float:
        # This method is unchanged
        total_weighted_score = 0.0
        for item in analysis_data:
            category, score = item.get("category_name"), item.get("score")
            if category in self.weights and isinstance(score, (int, float)):
                normalized_score = score / 5.0
                weight_percentage = self.weights[category] / 100.0
                total_weighted_score += normalized_score * weight_percentage
        return total_weighted_score

    def _interpret_final_score(self, score: float) -> str:
        # This method is unchanged
        if -1.0 <= score < -0.6: return "Strong Left Bias"
        if -0.6 <= score < -0.3: return "Moderate Left Bias"
        if -0.3 <= score < -0.1: return "Slight Left Bias"
        if -0.1 <= score <= 0.1: return "Neutral / Balanced"
        if 0.1 < score <= 0.3:  return "Slight Right Bias"
        if 0.3 < score <= 0.6:  return "Moderate Right Bias"
        if 0.6 < score <= 1.0:  return "Strong Right Bias"
        return "Indeterminate Score"

    # --- NEWLY ADDED METHOD ---
    def _display_results(self, analysis_data: List[Dict[str, Any]], final_score: float, judgment: str):
        """Displays the full analysis in a formatted table."""
        table = Table(
            title=f"[bold cyan]Bias Analysis Report for:[/] [dim]{self.source_url}[/dim]",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Category", style="dim", width=30)
        table.add_column("Weight", justify="center")
        table.add_column("Score (-5 to +5)", justify="center")
        table.add_column("Justification", style="italic")

        for item in analysis_data:
            score = item.get('score', 'N/A')
            score_color = "white"
            if isinstance(score, (int, float)):
                score_color = "red" if score < 0 else "blue" if score > 0 else "white"

            table.add_row(
                item.get('category_name', 'N/A'),
                f"{self.weights.get(item.get('category_name'), 0)}%",
                f"[{score_color}]{score}[/{score_color}]",
                item.get('justification', 'No justification provided.')
            )

        CONSOLE.print(table)
        CONSOLE.print("\n--- [bold]Final Judgment[/bold] ---")
        CONSOLE.print(f"Final Bias Index: [bold]{final_score:.3f}[/bold]")
        CONSOLE.print(f"Overall Assessment: [bold]{judgment}[/bold]\n")

    # --- UPDATED METHOD ---
    def run(self) -> Tuple[float, str] | None:
        """Orchestrates the analysis, displays the report, and returns the final score."""
        if not self.content:
            return None

        CONSOLE.print("[yellow]    Analyzing for bias...[/yellow]")
        prompt = self._generate_prompt()
        llm_response_str = self._call_llm(prompt)
        if not llm_response_str:
            return None

        analysis_data = self._parse_llm_response(llm_response_str)
        if not analysis_data:
            return None

        final_score = self._calculate_bias_score(analysis_data)
        judgment = self._interpret_final_score(final_score)

        # Call the display method before returning the values
        self._display_results(analysis_data, final_score, judgment)

        # Still return the values so main.py can use them for logic
        return final_score, judgment