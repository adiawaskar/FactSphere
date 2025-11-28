# agents/timeline/main.py
import json
import os
import shutil
import time
from .config import CONSOLE, CHROMA_DB_PATH, MAX_ITERATIONS, MAX_ARTICLES_PER_STEP
from .o0_query_refiner import refine_initial_query
from .o1_retrieval import get_urls_from_duckduckgo, extract_content_from_url
from .o2_vector_store import chunk_text, add_chunks_to_db, get_all_chunks_from_db
from .o3_event_extraction import extract_events_from_chunk
from .o4_graph_builder import Neo4jGraph
from .o5_narrative_generator import generate_narrative
from .o6_curiosity_agent import generate_curiosity_queries

def process_search_query(query: str, visited_urls: set, graph: Neo4jGraph) -> bool:
    """
    Helper function to run the pipeline for a single query.
    Returns True if new events were added, False otherwise.
    """
    article_infos = get_urls_from_duckduckgo(query, max_results=MAX_ARTICLES_PER_STEP)
    
    new_articles_found = False
    articles_to_process = []

    # Filter out already visited URLs
    for info in article_infos:
        if info['url'] not in visited_urls:
            visited_urls.add(info['url'])
            # Extract content
            article_data = extract_content_from_url(info['url'], info['published_at'])
            if article_data:
                articles_to_process.append(article_data)
                new_articles_found = True
    
    if not articles_to_process:
        CONSOLE.print(f"[grey50]   - No new articles found for query: {query}[/grey50]")
        return False

    # Chunk and Store
    current_chunks = []
    for article in articles_to_process:
        chunks = chunk_text(article)
        add_chunks_to_db(chunks)
        current_chunks.extend(chunks) # Keep track of just these chunks for extraction

    # Extract Events (Only from the NEW chunks to save LLM tokens/time)
    new_events = []
    CONSOLE.print(f"\n[yellow]   - Extracting events from {len(current_chunks)} new chunks...[/yellow]")
    for chunk in current_chunks:
        events = extract_events_from_chunk(chunk)
        if events:
            new_events.extend(events)

    # Add to Graph
    if new_events:
        CONSOLE.print(f"[green]   - Adding {len(new_events)} new events to Neo4j...[/green]")
        for event in new_events:
            graph.add_event(event)
        return True
    
    return False

def main(topic: str):
    CONSOLE.print("[bold yellow]🧹 Cleaning up previous data...[/bold yellow]")
    if os.path.exists(CHROMA_DB_PATH):
        shutil.rmtree(CHROMA_DB_PATH)
    
    graph = Neo4jGraph()
    graph.clear_database()
    CONSOLE.print("   - Environment ready.")

    visited_urls = set()
    
    # --- STEP 1: INITIAL REFINEMENT ---
    current_query = refine_initial_query(topic)
    queries_queue = [current_query]

    # --- STEP 2: ITERATIVE LOOP ---
    for i in range(MAX_ITERATIONS):
        CONSOLE.print(f"\n\n[bold blue]🌀 --- ITERATION {i+1} / {MAX_ITERATIONS} ---[/bold blue]")
        
        if not queries_queue:
            CONSOLE.print("[yellow]No queries left to process. Stopping early.[/yellow]")
            break
            
        # Copy current queue to batch and clear main queue
        current_batch_queries = queries_queue[:]
        queries_queue = [] 
        
        data_added_in_this_loop = False

        for query in current_batch_queries:
            success = process_search_query(query, visited_urls, graph)
            if success:
                data_added_in_this_loop = True
        
        # Connect temporal relationships after adding new data
        if data_added_in_this_loop:
            graph.add_temporal_relationships()

        # --- STEP 3: CURIOSITY CHECK ---
        # Don't run curiosity on the very last iteration
        if i < MAX_ITERATIONS - 1:
            if data_added_in_this_loop:
                # Ask the Curiosity Agent for new leads based on the UPDATED graph
                new_queries = generate_curiosity_queries(graph, i+1)
                queries_queue.extend(new_queries)
            else:
                CONSOLE.print("[red]   - No new data found in this loop. Stopping curiosity.[/red]")
                break
        
        time.sleep(2)

    # --- STEP 4: FINAL NARRATIVE ---
    CONSOLE.print("\n[yellow]✨ All iterations complete. Generating final report...[/yellow]")
    sorted_events = graph.get_sorted_events()
    
    if not sorted_events:
        CONSOLE.print("[bold red]No events were found after all iterations.[/bold red]")
    else:
        final_narrative = generate_narrative(sorted_events)
        CONSOLE.print("\n\n[bold magenta]🎉 --- FINAL NARRATIVE --- 🎉[/bold magenta]")
        print(json.dumps(final_narrative, indent=2))

    graph.close()

if __name__ == "__main__":
    news_topic = "Operation Sindoor" 
    main(news_topic)