# backend/services/timeline_service.py
import logging
import shutil
import os
from typing import Dict, Any

# These imports are for the timeline agent, which is in the root 'agents' folder
from backend.agents.timeline.o1_retrieval import get_urls_from_gnews, extract_content_from_url
from backend.agents.timeline.o2_vector_store import chunk_text, add_chunks_to_db, get_all_chunks_from_db
from backend.agents.timeline.o3_event_extraction import extract_events_from_chunk
from backend.agents.timeline.o4_graph_builder import Neo4jGraph
from backend.agents.timeline.o5_narrative_generator import generate_narrative
from backend.agents.timeline.config import CHROMA_DB_PATH

logger = logging.getLogger("timeline_service")

# In-memory storage for timeline job results
timeline_job_results: Dict[str, Dict[str, Any]] = {}

def run_timeline_generation_background(job_id: str, topic: str):
    """
    Orchestrates the entire timeline generation pipeline as a background task.
    """
    global timeline_job_results
    timeline_job_results[job_id] = {"status": "running", "topic": topic, "progress": "Initializing..."}
    logger.info(f"Job {job_id}: Starting timeline generation for '{topic}'")

    try:
        # === IMPORTANT: Cleanup stateful databases ===
        # This agent is stateful and clears previous data. This is a critical design point.
        # In a multi-user environment, this would cause race conditions.
        # For a single-user demo, this is acceptable.
        
        timeline_job_results[job_id]["progress"] = "Cleaning up previous data..."
        if os.path.exists(CHROMA_DB_PATH):
            shutil.rmtree(CHROMA_DB_PATH)
        graph = Neo4jGraph()
        graph.clear_database()
        logger.info(f"Job {job_id}: Cleared ChromaDB and Neo4j for new analysis.")

        # 1. RETRIEVAL
        timeline_job_results[job_id]["progress"] = "Step 1/5: Retrieving news articles..."
        article_infos = get_urls_from_gnews(topic, max_results=5)
        if not article_infos:
            raise ValueError("No articles found from GNews.")
        
        all_articles = [
            data for info in article_infos 
            if (data := extract_content_from_url(info['url'], info['published_at'])) is not None
        ]

        # 2. VECTOR STORE
        timeline_job_results[job_id]["progress"] = f"Step 2/5: Storing {len(all_articles)} articles in vector DB..."
        for article in all_articles:
            chunks = chunk_text(article)
            add_chunks_to_db(chunks)

        # 3. EVENT EXTRACTION
        all_chunks = get_all_chunks_from_db()
        timeline_job_results[job_id]["progress"] = f"Step 3/5: Extracting events from {len(all_chunks)} text chunks..."
        
        all_events = []
        for i, chunk in enumerate(all_chunks):
            timeline_job_results[job_id]["progress"] = f"Step 3/5: Extracting events... (chunk {i+1}/{len(all_chunks)})"
            if events := extract_events_from_chunk(chunk):
                all_events.extend(events)
        
        # 4. GRAPH CONSTRUCTION & REASONING
        timeline_job_results[job_id]["progress"] = f"Step 4/5: Building knowledge graph with {len(all_events)} events..."
        for event in all_events:
            graph.add_event(event)
        graph.add_temporal_relationships()

        # 5. NARRATIVE GENERATION
        timeline_job_results[job_id]["progress"] = "Step 5/5: Generating final narrative..."
        sorted_events = graph.get_sorted_events()
        final_narrative = generate_narrative(sorted_events)
        
        graph.close()

        # Store final results
        timeline_job_results[job_id]["status"] = "complete"
        timeline_job_results[job_id]["results"] = final_narrative
        logger.info(f"Job {job_id}: Timeline generation completed successfully.")

    except Exception as e:
        logger.error(f"Job {job_id}: An error occurred during timeline generation: {e}", exc_info=True)
        timeline_job_results[job_id]["status"] = "failed"
        timeline_job_results[job_id]["error"] = str(e)