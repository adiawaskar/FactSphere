# fact_checker_workflow.py

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple

# --- Third-party library imports ---
import trafilatura
import chromadb
from dotenv import load_dotenv
from groq import Groq, APIError
from rich.console import Console
from rich.table import Table
from googlesearch import search
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# --- Initial Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
CONSOLE = Console()

# --- Global Variables & Constants ---
# It is recommended to use models from Hugging Face's Sentence Transformers library.
# For a list of available pre-trained models, see: https://huggingface.co/sentence-transformers
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
CHROMA_DB_PATH = "neutral_knowledge_base"
COLLECTION_NAME = "neutral_articles"
NEUTRAL_BIAS_THRESHOLD = 0.1  # Articles with a score between -0.1 and 0.1 are considered neutral

# ==============================================================================
# 1. URL FETCHING & CONTENT EXTRACTION
# ==============================================================================

def get_google_urls(query: str, num_results: int = 10) -> List[str]:
    """Fetches Google search URLs for a given query."""
    CONSOLE.print(f"\n[yellow]🔍 Searching for '{query}'...[/yellow]")
    try:
        return list(search(query, num_results=num_results))
    except Exception as e:
        CONSOLE.print(f"[bold red]Error during Google search: {e}[/bold red]")
        return []

def extract_content_from_url(url: str) -> str | None:
    """Extracts the main text content from a URL using trafilatura."""
    CONSOLE.print(f"--> [cyan]Extracting content from:[/cyan] {url}")
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        CONSOLE.print("[red]    Error: Could not retrieve the webpage.[/red]")
        return None
    text = trafilatura.extract(
        downloaded, include_comments=False, include_tables=False, no_fallback=True
    )
    if text:
        CONSOLE.print("[green]    --> Successfully extracted content.[/green]")
        return text
    else:
        CONSOLE.print("[red]    Error: Could not extract main content.[/red]")
        return None

# ==============================================================================
# 2. BIAS ANALYSIS AGENT
# ==============================================================================

class BiasAnalysisAgent:
    """
    An AI agent that analyzes news articles for bias using an LLM
    based on a predefined 13-point framework.
    """
    def __init__(self, content: str, model: str = 'llama3-8b-8192'):
        self.content = content
        self.model = model
        self.client = self._initialize_groq_client()
        self.weights = {
            'Title Analysis': 5, 'Authorship': 5, 'Word Choice & Tone': 15,
            'Framing & Context': 10, 'Sources & Attribution': 15,
            'Omission & Agenda': 10, 'Placement & Visuals': 5, 'Labeling': 5,
            'Moral & Value Appeals': 10, 'Sentiment Toward Political Actors': 10,
            'Narrative Construction': 5, 'Fact vs Opinion': 10, 'Confirmation Bias': 5
        }

    def _initialize_groq_client(self) -> Groq:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logging.error("GROQ_API_KEY not found in .env file.")
            CONSOLE.print("[bold red]Error: GROQ_API_KEY environment variable is not set.[/bold red]")
            sys.exit(1)
        return Groq(api_key=api_key)

    def _generate_prompt(self) -> str:
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
        **Framework for Analysis:**
        {framework_details}
        **Instructions:**
        For each of the 13 categories, you must provide:
        1. A `score` from -5 to +5, where -5 is strong left-leaning, +5 is strong right-leaning, and 0 is neutral.
        2. A concise `justification` (1-2 sentences).
        Your entire output **MUST** be a single, valid JSON object containing a list named "analysis_results". Do not include any text or explanations outside of this JSON structure.
        **Article to Analyze:**
        ---
        {self.content}
        ---
        """

    def _call_llm(self, prompt: str) -> str | None:
        try:
            completion = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}],
                temperature=0.1, response_format={"type": "json_object"},
            )
            return completion.choices[0].message.content
        except APIError as e:
            CONSOLE.print(f"[bold red]An error occurred with the Groq API: {e}[/bold red]")
            return None

    def _parse_llm_response(self, response_text: str) -> List[Dict[str, Any]] | None:
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
        total_weighted_score = 0.0
        for item in analysis_data:
            category, score = item.get("category_name"), item.get("score")
            if category in self.weights and isinstance(score, (int, float)):
                normalized_score = score / 5.0
                weight_percentage = self.weights[category] / 100.0
                total_weighted_score += normalized_score * weight_percentage
        return total_weighted_score

    def _interpret_final_score(self, score: float) -> str:
        if -1.0 <= score < -0.6: return "Strong Left Bias"
        if -0.6 <= score < -0.3: return "Moderate Left Bias"
        if -0.3 <= score < -0.1: return "Slight Left Bias"
        if -0.1 <= score <= 0.1: return "Neutral / Balanced"
        if 0.1 < score <= 0.3:  return "Slight Right Bias"
        if 0.3 < score <= 0.6:  return "Moderate Right Bias"
        if 0.6 < score <= 1.0:  return "Strong Right Bias"
        return "Indeterminate Score"

    def run(self) -> Tuple[float, str] | None:
        """Orchestrates the analysis and returns the final score and judgment."""
        if not self.content: return None
        CONSOLE.print("[yellow]    Analyzing for bias...[/yellow]")
        prompt = self._generate_prompt()
        llm_response_str = self._call_llm(prompt)
        if not llm_response_str: return None
        analysis_data = self._parse_llm_response(llm_response_str)
        if not analysis_data: return None
        final_score = self._calculate_bias_score(analysis_data)
        judgment = self._interpret_final_score(final_score)
        CONSOLE.print(f"    --> [bold]Bias Assessment:[/] [bold]{judgment}[/] (Score: {final_score:.3f})")
        return final_score, judgment

# ==============================================================================
# 3. NEUTRAL KNOWLEDGE BASE (CHROMA DB)
# ==============================================================================

class KnowledgeBase:
    """Manages the ChromaDB vector store for neutral articles."""
    def __init__(self, path: str, collection_name: str):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=70)
        CONSOLE.print(f"[green]✅ Knowledge Base initialized at '{path}'.[/green]")

    def add_document(self, content: str, source_url: str):
        """Chunks, embeds, and adds a neutral document to the collection, avoiding duplicates."""
        chunks = self.text_splitter.split_text(content)
        if not chunks:
            return

        # Simple duplicate check by hashing the first chunk
        first_chunk_hash = hashlib.md5(chunks[0].encode()).hexdigest()
        if self.collection.get(ids=[first_chunk_hash])['ids']:
            CONSOLE.print("[yellow]    Skipping duplicate document.[/yellow]")
            return

        embeddings = EMBEDDING_MODEL.encode(chunks).tolist()
        ids = [hashlib.md5(chunk.encode()).hexdigest() for chunk in chunks]
        metadatas = [{"source": source_url} for _ in chunks]
        
        self.collection.add(embeddings=embeddings, documents=chunks, metadatas=metadatas, ids=ids)
        CONSOLE.print(f"[green]    --> Added {len(chunks)} chunks to the neutral knowledge base.[/green]")

    def query(self, misconception: str, n_results: int = 5) -> List[str]:
        """Queries the knowledge base for relevant neutral chunks."""
        results = self.collection.query(query_texts=[misconception], n_results=n_results)
        return results['documents'][0] if results['documents'] else []

# ==============================================================================
# 4. BIASED CONTENT PROCESSING & FACT-CHECKING
# ==============================================================================

def generate_misconceptions(biased_content: str) -> List[str]:
    """
    Uses an LLM to simulate a naive reader and generate leading questions or
    misconceptions from biased content.
    """
    CONSOLE.print("[yellow]    Generating misconceptions from biased content...[/yellow]")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = f"""
    You are a naive reader who trusts everything and reacts emotionally to biased framing.
    Read the following article. Based on its biased or emotionally loaded content, generate 2-3
    leading questions or common misconceptions that someone might form after reading it.
    Your output MUST be a JSON object with a single key "misconceptions" which is a list of strings.

    Article:
    ---
    {biased_content[:4000]}
    ---
    """
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192", messages=[{"role": "user", "content": prompt}],
            temperature=0.7, response_format={"type": "json_object"},
        )
        response = json.loads(completion.choices[0].message.content)
        misconceptions = response.get("misconceptions", [])
        for q in misconceptions:
            CONSOLE.print(f"    --> [magenta]Generated Question:[/magenta] {q}")
        return misconceptions
    except (APIError, json.JSONDecodeError, KeyError) as e:
        CONSOLE.print(f"[bold red]Error generating misconceptions: {e}[/bold red]")
        return []

def generate_fact_check_report(misconception: str, neutral_chunks: List[str], source_url: str):
    """
    Generates a fact-check report using retrieved neutral evidence to address a misconception.
    """
    CONSOLE.print(f"\n[cyan]Generating Fact-Check Report for:[/cyan] '{misconception}'")
    if not neutral_chunks:
        CONSOLE.print("[yellow]Warning: No neutral reporting available to fact-check this claim.[/yellow]")
        return

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    context = "\n\n---\n\n".join(neutral_chunks)
    prompt = f"""
    You are a fact-checker. Your goal is to provide a balanced, evidence-based correction to a misconception.
    Use the "Neutral Evidence" provided below to address the "Misconception Question".

    Misconception Question: "{misconception}"
    Biased Source: {source_url}

    Neutral Evidence:
    ---
    {context}
    ---

    Instructions:
    1.  **Correction**: Write a clear, neutral paragraph that corrects the misconception. Add nuance and point out missing facts.
    2.  **Confidence Score**: Provide a confidence score (e.g., "High", "Medium", "Low") based on how well the neutral evidence addresses the question.
    3.  **Balanced Summary**: Summarize the situation by acknowledging its complexity but stating what multiple sources confirm.

    Your output MUST be a single, valid JSON object with three keys: "correction", "confidence_score", and "balanced_summary".
    """
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192", messages=[{"role": "user", "content": prompt}],
            temperature=0.2, response_format={"type": "json_object"},
        )
        report = json.loads(completion.choices[0].message.content)

        # --- Display User-Facing Output ---
        CONSOLE.print("\n" + "="*50)
        CONSOLE.print("[bold underline]Fact-Check Report[/bold underline]\n")
        CONSOLE.print(f"[bold red]Misconception:[/bold red] {misconception}")
        CONSOLE.print(f"([italic]Originating from biased source: {source_url}[/italic])\n")
        CONSOLE.print(f"[bold green]Correction:[/bold green] {report.get('correction', 'N/A')}\n")
        CONSOLE.print(f"[bold]Confidence Score:[/bold] {report.get('confidence_score', 'N/A')}")
        CONSOLE.print(f"[bold]Balanced Summary:[/bold] {report.get('balanced_summary', 'N/A')}\n")
        CONSOLE.print(f"[bold blue]Evidence Based On:[/bold blue] Neutral Knowledge Base")
        CONSOLE.print("="*50 + "\n")

    except (APIError, json.JSONDecodeError, KeyError) as e:
        CONSOLE.print(f"[bold red]Error generating fact-check report: {e}[/bold red]")


# ==============================================================================
# 5. MAIN WORKFLOW ORCHESTRATION
# ==============================================================================

def main():
    """Main function to run the entire workflow."""
    # --- Setup ---
    kb = KnowledgeBase(path=CHROMA_DB_PATH, collection_name=COLLECTION_NAME)
    biased_articles_for_review = [] # Store tuples of (content, url)

    # --- User Input ---
    topic = input("Enter a topic to research: ")
    if not topic:
        CONSOLE.print("[bold red]Topic cannot be empty.[/bold red]")
        return

    # --- Stage 1: Data Collection & Bias Analysis ---
    CONSOLE.print("\n--- [bold]Stage 1: Collecting and Analyzing Articles[/bold] ---")
    urls = get_google_urls(topic)
    for url in urls:
        content = extract_content_from_url(url)
        if not content:
            continue

        agent = BiasAnalysisAgent(content)
        analysis_result = agent.run()
        if not analysis_result:
            continue

        final_score, _ = analysis_result
        if abs(final_score) <= NEUTRAL_BIAS_THRESHOLD:
            kb.add_document(content, url)
        else:
            biased_articles_for_review.append((content, url))

    # --- Stage 2: Fact-Checking Biased Content ---
    CONSOLE.print("\n--- [bold]Stage 2: Generating Fact-Checks from Biased Articles[/bold] ---")
    if not biased_articles_for_review:
        CONSOLE.print("[green]No significantly biased articles were found to fact-check.[/green]")
        return

    for biased_content, biased_url in biased_articles_for_review:
        misconceptions = generate_misconceptions(biased_content)
        for misconception in misconceptions:
            relevant_chunks = kb.query(misconception)
            generate_fact_check_report(misconception, relevant_chunks, biased_url)

if __name__ == "__main__":
    main()