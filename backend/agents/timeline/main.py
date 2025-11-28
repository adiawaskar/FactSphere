# #agents/timeline/main.py
# import json
# import os
# import shutil
# from .config import CONSOLE, CHROMA_DB_PATH
# from .o1_retrieval import get_urls_from_gnews, extract_content_from_url
# from .o2_vector_store import chunk_text, add_chunks_to_db, get_all_chunks_from_db
# from .o3_event_extraction import extract_events_from_chunk
# from .o4_graph_builder import Neo4jGraph
# from .o5_narrative_generator import generate_narrative

# def main(topic: str, max_articles: int = 5):
#     """
#     Main pipeline to process a news topic and generate a timeline.
#     """
#     CONSOLE.print("[bold yellow]🧹 Cleaning up previous data...[/bold yellow]")

#     # 1. Clean ChromaDB by deleting the directory
#     if os.path.exists(CHROMA_DB_PATH):
#         shutil.rmtree(CHROMA_DB_PATH)
#         CONSOLE.print(f"   - Removed ChromaDB directory: {CHROMA_DB_PATH}")

#     # 2. Clean Neo4j Database by clearing all nodes
#     graph = Neo4jGraph()
#     graph.clear_database()
#     CONSOLE.print("   - Cleared all nodes and relationships from Neo4j.")
#     # 1. RETRIEVAL LAYER
#     article_infos = get_urls_from_gnews(topic, max_results=max_articles)

#     if not article_infos:
#         CONSOLE.print("[bold red]No articles found from GNews. Exiting pipeline.[/bold red]")
#         return
    
#     all_articles = []
#     for info in article_infos:
#         article_data = extract_content_from_url(info['url'], info['published_at'])
#         if article_data:
#             all_articles.append(article_data)

#     # 2. VECTOR STORE LAYER
#     for article in all_articles:
#         chunks = chunk_text(article)
#         add_chunks_to_db(chunks)

#     # 3. EVENT EXTRACTION LAYER
#     all_chunks = get_all_chunks_from_db()
#     all_events = []
#     CONSOLE.print(f"\n[yellow] extracting events from {len(all_chunks)} chunks...[/yellow]")
#     for chunk in all_chunks:
#         events = extract_events_from_chunk(chunk)
#         if events:
#             all_events.extend(events)
    
#     CONSOLE.print(f"[green]   --> Extracted a total of {len(all_events)} potential events.[/green]")

#     # 4. NEO4J GRAPH CONSTRUCTION
#     # graph = Neo4jGraph()
#     CONSOLE.print("\n[yellow]🏗️ Building knowledge graph in Neo4j...[/yellow]")
#     for event in all_events:
#         graph.add_event(event)

#     # 5. TEMPORAL REASONING
#     graph.add_temporal_relationships()
#     CONSOLE.print("[green]   --> Graph construction complete.[/green]")

#     # 6. NARRATIVE GENERATION
#     # This step is missing from your main function, so I've added it.
#     # You would need a narrative generator module. For now, let's just get the events.
#     sorted_events = graph.get_sorted_events()
    
#     # Assuming you have a narrative generator module as described in the plan
#     from o5_narrative_generator import generate_narrative 
#     final_narrative = generate_narrative(sorted_events)

#     # 7. OUTPUT
#     CONSOLE.print("\n\n[bold magenta]🎉 --- FINAL NARRATIVE --- 🎉[/bold magenta]")
#     print(json.dumps(final_narrative, indent=2))

#     # Clean up
#     graph.close()


# if __name__ == "__main__":
#     news_topic = "Operation Sindoor"
#     main(news_topic)

# agents/timeline/main.py
import json
import os
import shutil
from .config import CONSOLE, CHROMA_DB_PATH
# --- CHANGE HERE: Import the new DDG function ---
from .o1_retrieval import get_urls_from_duckduckgo, extract_content_from_url
from .o2_vector_store import chunk_text, add_chunks_to_db, get_all_chunks_from_db
from .o3_event_extraction import extract_events_from_chunk
from .o4_graph_builder import Neo4jGraph
from .o5_narrative_generator import generate_narrative

def main(topic: str, max_articles: int = 5):
    """
    Main pipeline to process a news topic and generate a timeline.
    """
    CONSOLE.print("[bold yellow]🧹 Cleaning up previous data...[/bold yellow]")

    # 1. Clean ChromaDB
    if os.path.exists(CHROMA_DB_PATH):
        shutil.rmtree(CHROMA_DB_PATH)
        CONSOLE.print(f"   - Removed ChromaDB directory: {CHROMA_DB_PATH}")

    # 2. Clean Neo4j
    graph = Neo4jGraph()
    graph.clear_database()
    CONSOLE.print("   - Cleared all nodes and relationships from Neo4j.")
    
    # 1. RETRIEVAL LAYER (Changed to DuckDuckGo)
    article_infos = get_urls_from_duckduckgo(topic, max_results=max_articles)

    if not article_infos:
        CONSOLE.print("[bold red]No articles found. Exiting pipeline.[/bold red]")
        return
    
    all_articles = []
    for info in article_infos:
        article_data = extract_content_from_url(info['url'], info['published_at'])
        if article_data:
            all_articles.append(article_data)

    # 2. VECTOR STORE LAYER
    for article in all_articles:
        chunks = chunk_text(article)
        add_chunks_to_db(chunks)

    # ... (Rest of the file remains exactly the same) ...
    
    # 3. EVENT EXTRACTION LAYER
    all_chunks = get_all_chunks_from_db()
    all_events = []
    CONSOLE.print(f"\n[yellow] extracting events from {len(all_chunks)} chunks...[/yellow]")
    for chunk in all_chunks:
        events = extract_events_from_chunk(chunk)
        if events:
            all_events.extend(events)
    
    CONSOLE.print(f"[green]   --> Extracted a total of {len(all_events)} potential events.[/green]")

    # 4. NEO4J GRAPH CONSTRUCTION
    CONSOLE.print("\n[yellow]🏗️ Building knowledge graph in Neo4j...[/yellow]")
    for event in all_events:
        graph.add_event(event)

    # 5. TEMPORAL REASONING
    graph.add_temporal_relationships()
    CONSOLE.print("[green]   --> Graph construction complete.[/green]")

    # 6. NARRATIVE GENERATION
    sorted_events = graph.get_sorted_events()
    final_narrative = generate_narrative(sorted_events)

    # 7. OUTPUT
    CONSOLE.print("\n\n[bold magenta]🎉 --- FINAL NARRATIVE --- 🎉[/bold magenta]")
    print(json.dumps(final_narrative, indent=2))

    # Clean up
    graph.close()

if __name__ == "__main__":
    news_topic = "Operation Sindoor"
    main(news_topic)