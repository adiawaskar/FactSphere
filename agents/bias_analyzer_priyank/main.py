# agents/bias_analyzer_priyank/main.py
import google.generativeai as genai
from config import CONSOLE, NEUTRAL_BIAS_THRESHOLD, GEMINI_API_KEY
from query_enhancer import enhance_query
from news_fetcher import get_urls_from_google_search, get_urls_from_gnews
from content_extractor import extract_content_from_url
from bias_analyzer import BiasAnalysisAgent
from knowledge_base import KnowledgeBase
from fact_checker import generate_misconceptions, generate_fact_check_report

def main():
    """Main function to run the entire workflow."""
    kb = KnowledgeBase()
    biased_articles_for_review = []
    urls = []

    # --- Configure API ---
    if not GEMINI_API_KEY:
        CONSOLE.print("[bold red]GEMINI_API_KEY is not configured in your environment. Exiting.[/bold red]")
        return
    genai.configure(api_key=GEMINI_API_KEY)
    CONSOLE.print("[green]✅ Gemini API configured.[/green]")


    # --- User Input Stage ---
    topic = input("Enter a topic to research: ")
    if not topic:
        CONSOLE.print("[bold red]Topic cannot be empty.[/bold red]")
        return

    # --- Engine Selection ---
    while True:
        engine = input("Choose a search engine ('google' or 'gnews'): ").lower().strip()
        if engine in ["google", "gnews"]:
            break
        CONSOLE.print("[bold red]Invalid choice. Please enter 'google' or 'gnews'.[/bold red]")

    # --- Stage 1: Collecting and Analyzing Articles ---
    CONSOLE.print("\n--- [bold]Stage 1: Collecting and Analyzing Articles[/bold] ---")
    
    # Fetch URLs based on the selected engine
    if engine == 'google':
        enhanced_query = enhance_query(topic)
        urls = get_urls_from_google_search(enhanced_query)
    elif engine == 'gnews':
        # GNews works better with the raw topic
        urls = get_urls_from_gnews(topic)

    if not urls:
        CONSOLE.print(f"[bold red]Could not fetch any article URLs using {engine}. Exiting.[/bold red]")
        return

    # The rest of the workflow remains the same
    for url in urls:
        content = extract_content_from_url(url)
        if not content:
            continue

        agent = BiasAnalysisAgent(content, source_url=url)
        analysis_result = agent.run()
        if not analysis_result:
            continue

        final_score, _ = analysis_result
        if abs(final_score) <= NEUTRAL_BIAS_THRESHOLD:
            kb.add_document(content, url)
        else:
            biased_articles_for_review.append((content, url))

    # --- Stage 2: Generating Fact-Checks from Biased Articles ---
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