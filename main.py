# import os
# import sys
# import json
# import logging
# from pathlib import Path
# from typing import Dict, List, Any

# from dotenv import load_dotenv
# from groq import Groq, APIError
# from rich.console import Console
# from rich.table import Table

# # --- Configuration ---
# load_dotenv()
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# CONSOLE = Console()

# class BiasAnalysisAgent:
#     """
#     An AI agent that analyzes news articles for bias using an LLM
#     based on a predefined 13-point framework.
#     """
#     def __init__(self, file_path: str, model: str = 'llama3-8b-8192'):
#         self.file_path = Path(file_path)
#         self.model = model
#         self.content = self._read_content()
#         self.client = self._initialize_groq_client()
#         self.weights = {
#             'Title Analysis': 5, 'Authorship': 5, 'Word Choice & Tone': 15,
#             'Framing & Context': 10, 'Sources & Attribution': 15,
#             'Omission & Agenda': 10, 'Placement & Visuals': 5, 'Labeling': 5,
#             'Moral & Value Appeals': 10, 'Sentiment Toward Political Actors': 10,
#             'Narrative Construction': 5, 'Fact vs Opinion': 10, 'Confirmation Bias': 5
#         }

#     def _initialize_groq_client(self) -> Groq:
#         """Initializes the Groq client and handles missing API key."""
#         api_key = os.getenv("GROQ_API_KEY")
#         if not api_key:
#             logging.error("GROQ_API_KEY not found in .env file.")
#             CONSOLE.print("[bold red]Error: GROQ_API_KEY environment variable is not set.[/bold red]")
#             sys.exit(1)
#         return Groq(api_key=api_key)

#     def _read_content(self) -> str:
#         """Reads content from the specified file path."""
#         try:
#             return self.file_path.read_text(encoding='utf-8')
#         except FileNotFoundError:
#             logging.error(f"File not found at: {self.file_path}")
#             CONSOLE.print(f"[bold red]Error: File '{self.file_path}' not found.[/bold red]")
#             sys.exit(1)
#         except Exception as e:
#             logging.error(f"Could not read file: {e}")
#             CONSOLE.print(f"[bold red]Error reading file: {e}[/bold red]")
#             sys.exit(1)

#     def _generate_prompt(self) -> str:
#         """Generates the detailed prompt for the LLM based on the framework."""
#         framework_details = """
#         1.  **Title Analysis**: Is it neutral or judgmental?
#         2.  **Authorship**: Is the author named and credible?
#         3.  **Word Choice & Tone**: Are words loaded/emotive or neutral?
#         4.  **Framing & Context**: How is the event framed (e.g., riot vs. protest)? Is context selective?
#         5.  **Sources & Attribution**: Are sources balanced and credible? Are quotes attributed?
#         6.  **Omission & Agenda Setting**: Are important facts or perspectives missing?
#         7.  **Placement & Visuals**: Is story placement prominent or buried? (Analyze based on text structure).
#         8.  **Labeling**: Are ideological labels used (e.g., "far-right," "radical left")?
#         9.  **Moral & Value Appeals**: Does it appeal to left-leaning (fairness, equality) or right-leaning (tradition, patriotism) values?
#         10. **Sentiment Toward Political Actors**: Is sentiment positive, negative, or neutral toward parties/leaders?
#         11. **Narrative Construction**: Is it a one-sided "heroes vs. villains" story?
#         12. **Fact vs. Opinion**: Is the article based on verifiable facts or speculation/commentary?
#         13. **Confirmation Bias Check**: Does it only reinforce one worldview without acknowledging complexities?
#         """

#         return f"""
#         You are a meticulous and impartial media bias analyst. Your task is to analyze the provided news article based on a strict 13-point framework.

#         **Framework for Analysis:**
#         {framework_details}

#         **Instructions:**
#         For each of the 13 categories, you must provide:
#         1. A `score` from -5 to +5, where:
#            - Negative values (-) indicate a left-leaning bias.
#            - Positive values (+) indicate a right-leaning bias.
#            - 0 indicates neutrality or balance.
#            - The magnitude (-5 to 5) represents the strength of the bias (e.g., -5 is strong left, +1 is slight right).
#         2. A concise `justification` (1-2 sentences) explaining your score.

#         Your entire output **MUST** be a single, valid JSON object containing a list named "analysis_results". Each item in the list should be an object with three keys: "category_name", "score", and "justification". Do not include any text or explanations outside of this JSON structure.

#         **Article to Analyze:**
#         ---
#         {self.content}
#         ---
#         """

#     def _call_llm(self, prompt: str) -> str | None:
#         """Calls the Groq API with the specified prompt and returns the JSON response."""
#         try:
#             completion = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.1,
#                 response_format={"type": "json_object"},
#             )
#             return completion.choices[0].message.content
#         except APIError as e:
#             logging.error(f"Groq API Error: {e}")
#             CONSOLE.print(f"[bold red]An error occurred with the Groq API: {e}[/bold red]")
#             return None
#         except Exception as e:
#             logging.error(f"An unexpected error occurred during API call: {e}")
#             CONSOLE.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
#             return None

#     def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]] | None:
#         """Parses the JSON string from the LLM into a Python dictionary."""
#         try:
#             data = json.loads(response_text)
#             # Basic validation of the returned structure
#             if "analysis_results" in data and isinstance(data["analysis_results"], list):
#                 return data["analysis_results"]
#             else:
#                 logging.error("LLM response did not contain 'analysis_results' list.")
#                 return None
#         except json.JSONDecodeError:
#             logging.error(f"Failed to decode LLM response into JSON. Response:\n{response_text}")
#             CONSOLE.print("[bold red]Error: The LLM returned an invalid JSON response.[/bold red]")
#             return None

#     def _calculate_bias_score(self, analysis_data: List[Dict[str, Any]]) -> float:
#         """Calculates the final weighted bias index from the analysis data."""
#         total_weighted_score = 0.0
#         for item in analysis_data:
#             category = item.get("category_name")
#             score = item.get("score")
#             if category in self.weights and isinstance(score, (int, float)):
#                 # Normalize score from [-5, 5] to [-1, 1] range
#                 normalized_score = score / 5.0
#                 weight_percentage = self.weights[category] / 100.0
#                 total_weighted_score += normalized_score * weight_percentage
#             else:
#                 logging.warning(f"Skipping invalid category or score in LLM data: {item}")
#         return total_weighted_score

#     def _interpret_final_score(self, score: float) -> str:
#         """Interprets the final score into a human-readable judgment."""
#         if -1.0 <= score < -0.6: return "Strong Left Bias"
#         if -0.6 <= score < -0.3: return "Moderate Left Bias"
#         if -0.3 <= score < -0.1: return "Slight Left Bias"
#         if -0.1 <= score <= 0.1: return "Neutral / Balanced"
#         if 0.1 < score <= 0.3:  return "Slight Right Bias"
#         if 0.3 < score <= 0.6:  return "Moderate Right Bias"
#         if 0.6 < score <= 1.0:  return "Strong Right Bias"
#         return "Indeterminate Score"

#     def _display_results(self, analysis_data: List[Dict[str, Any]], final_score: float, judgment: str):
#         """Displays the full analysis in a formatted table."""
#         table = Table(title="[bold cyan]Bias Analysis Report[/bold cyan]", show_header=True, header_style="bold magenta")
#         table.add_column("Category", style="dim", width=30)
#         table.add_column("Weight", justify="center")
#         table.add_column("Score (-5 to +5)", justify="center")
#         table.add_column("Justification", style="italic")

#         for item in analysis_data:
#             score = item.get('score', 'N/A')
#             score_color = "red" if score < 0 else "blue" if score > 0 else "white"
#             table.add_row(
#                 item.get('category_name', 'N/A'),
#                 f"{self.weights.get(item.get('category_name'), 0)}%",
#                 f"[{score_color}]{score}[/{score_color}]",
#                 item.get('justification', 'No justification provided.')
#             )

#         CONSOLE.print(table)
#         CONSOLE.print("\n--- [bold]Final Judgment[/bold] ---")
#         CONSOLE.print(f"Final Bias Index: [bold]{final_score:.3f}[/bold]")
#         CONSOLE.print(f"Overall Assessment: [bold]{judgment}[/bold]\n")

#     def run(self):
#         """Orchestrates the entire analysis process."""
#         if not self.content:
#             return

#         CONSOLE.print(f"[yellow]Analyzing '{self.file_path.name}' with {self.model}...[/yellow]")
#         prompt = self._generate_prompt()
#         llm_response_str = self._call_llm(prompt)

#         if not llm_response_str:
#             CONSOLE.print("[bold red]Analysis failed: Could not get a valid response from the LLM.[/bold red]")
#             return

#         analysis_data = self._parse_llm_response(llm_response_str)
#         if not analysis_data:
#             CONSOLE.print("[bold red]Analysis failed: Could not parse the LLM's response.[/bold red]")
#             return

#         final_score = self._calculate_bias_score(analysis_data)
#         judgment = self._interpret_final_score(final_score)
#         self._display_results(analysis_data, final_score, judgment)

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         CONSOLE.print("[bold yellow]Usage: python main.py <path_to_content_file>[/bold yellow]")
#         CONSOLE.print("Defaulting to 'content.txt'...")
#         input_file = "content.txt"
#     else:
#         input_file = sys.argv[1]

#     agent = BiasAnalysisAgent(file_path=input_file)
#     agent.run()
############################################
# # main.py
# from config import CONSOLE, NEUTRAL_BIAS_THRESHOLD
# from query_enhancer import enhance_query
# from content_extractor import get_google_urls, extract_content_from_url
# from bias_analyzer import BiasAnalysisAgent
# from knowledge_base import KnowledgeBase
# from fact_checker import generate_misconceptions, generate_fact_check_report

# def main():
#     """Main function to run the entire workflow."""
#     # --- Setup ---
#     kb = KnowledgeBase()
#     biased_articles_for_review = []

#     # --- User Input ---
#     topic = input("Enter a topic to research: ")
#     if not topic:
#         CONSOLE.print("[bold red]Topic cannot be empty.[/bold red]")
#         return

#     # --- Stage 1: Data Collection & Bias Analysis ---
#     CONSOLE.print("\n--- [bold]Stage 1: Collecting and Analyzing Articles[/bold] ---")
#     enhanced_query = enhance_query(topic)
#     urls = get_google_urls(enhanced_query)
    
#     for url in urls:
#         content = extract_content_from_url(url)
#         if not content:
#             continue

#         agent = BiasAnalysisAgent(content)
#         analysis_result = agent.run()
#         if not analysis_result:
#             continue

#         final_score, _ = analysis_result
#         if abs(final_score) <= NEUTRAL_BIAS_THRESHOLD:
#             kb.add_document(content, url)
#         else:
#             biased_articles_for_review.append((content, url))

#     # --- Stage 2: Fact-Checking Biased Content ---
#     CONSOLE.print("\n--- [bold]Stage 2: Generating Fact-Checks from Biased Articles[/bold] ---")
#     if not biased_articles_for_review:
#         CONSOLE.print("[green]No significantly biased articles were found to fact-check.[/green]")
#         return
#     if kb.collection.count() == 0:
#         CONSOLE.print("[yellow]No neutral articles were found to build a knowledge base for fact-checking.[/yellow]")
#         return

#     for biased_content, biased_url in biased_articles_for_review:
#         misconceptions = generate_misconceptions(biased_content)
#         for misconception in misconceptions:
#             relevant_chunks = kb.query(misconception)
#             generate_fact_check_report(misconception, relevant_chunks, biased_url)

# if __name__ == "__main__":
#     main()

# main.py
from config import CONSOLE, NEUTRAL_BIAS_THRESHOLD
from query_enhancer import enhance_query
from content_extractor import get_google_urls, extract_content_from_url
from bias_analyzer import BiasAnalysisAgent
from knowledge_base import KnowledgeBase
from fact_checker import generate_misconceptions, generate_fact_check_report

def main():
    """Main function to run the entire workflow."""
    kb = KnowledgeBase()
    biased_articles_for_review = []

    topic = input("Enter a topic to research: ")
    if not topic:
        CONSOLE.print("[bold red]Topic cannot be empty.[/bold red]")
        return

    CONSOLE.print("\n--- [bold]Stage 1: Collecting and Analyzing Articles[/bold] ---")
    enhanced_query = enhance_query(topic)
    urls = get_google_urls(enhanced_query)
    
    for url in urls:
        content = extract_content_from_url(url)
        if not content:
            continue

        # --- THIS LINE IS UPDATED ---
        # Pass the url for better reporting context
        agent = BiasAnalysisAgent(content, source_url=url)
        analysis_result = agent.run()
        if not analysis_result:
            continue

        final_score, _ = analysis_result
        if abs(final_score) <= NEUTRAL_BIAS_THRESHOLD:
            kb.add_document(content, url)
        else:
            biased_articles_for_review.append((content, url))

    CONSOLE.print("\n--- [bold]Stage 2: Generating Fact-Checks from Biased Articles[/bold] ---")
    if not biased_articles_for_review:
        CONSOLE.print("[green]No significantly biased articles were found to fact-check.[/green]")
        return
    if kb.collection.count() == 0:
        CONSOLE.print("[yellow]No neutral articles were found to build a knowledge base for fact-checking.[/yellow]")
        return

    for biased_content, biased_url in biased_articles_for_review:
        misconceptions = generate_misconceptions(biased_content)
        for misconception in misconceptions:
            relevant_chunks = kb.query(misconception)
            generate_fact_check_report(misconception, relevant_chunks, biased_url)

if __name__ == "__main__":
    main()