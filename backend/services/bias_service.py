# backend/services/bias_service.py
import logging
import uuid
from typing import Dict, Any

# --- Add the agent's path to system path ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# ---

from agents.bias_analyzer_priyank.content_extractor import extract_content_from_url
from agents.bias_analyzer_priyank.bias_analyzer import BiasAnalysisAgent
from agents.bias_analyzer_priyank.news_fetcher import get_urls_from_gnews
from agents.bias_analyzer_priyank.config import NEUTRAL_BIAS_THRESHOLD
from agents.bias_analyzer_priyank.knowledge_base import KnowledgeBase
from agents.bias_analyzer_priyank.fact_checker import generate_misconceptions, generate_fact_check_report

# Configure logging
logger = logging.getLogger("bias_service")

# In-memory storage for job results (for simplicity)
# In a production environment, you would use Redis, a database, or another persistent store.
job_results: Dict[str, Dict[str, Any]] = {}

def analyze_single_url(url: str) -> Dict[str, Any]:
    """
    Analyzes a single URL for bias and returns the results.
    This is a synchronous operation.
    """
    logger.info(f"Starting single URL analysis for: {url}")
    content = extract_content_from_url(url)
    if not content:
        logger.error(f"Could not extract content from {url}")
        return {"success": False, "message": "Could not extract content from URL."}

    # We need to adapt the agent to return JSON instead of printing
    agent = BiasAnalysisAgent(content, source_url=url)
    analysis_result = agent.run_for_api() # We will create this new method

    if not analysis_result:
        logger.error(f"Bias analysis failed for {url}")
        return {"success": False, "message": "Bias analysis failed."}

    return {"success": True, "result": analysis_result}


def run_topic_analysis_background(job_id: str, topic: str):
    """
    The main background task for analyzing a full topic.
    It fetches multiple articles, analyzes them, builds a knowledge base,
    and performs fact-checking.
    """
    job_results[job_id] = {"status": "running", "topic": topic, "results": {}}
    logger.info(f"Job {job_id}: Starting topic analysis for '{topic}'")

    try:
        kb = KnowledgeBase()
        biased_articles_for_review = []
        neutral_articles_for_kb = []
        all_analyses = []

        urls = get_urls_from_gnews(topic)
        if not urls:
            raise ValueError("Could not fetch any article URLs.")

        for i, url in enumerate(urls):
            job_results[job_id]["progress"] = f"Analyzing URL {i+1}/{len(urls)}: {url}"
            content = extract_content_from_url(url)
            if not content:
                continue

            agent = BiasAnalysisAgent(content, source_url=url)
            analysis_result = agent.run_for_api()
            if not analysis_result:
                continue
            
            all_analyses.append(analysis_result)
            final_score = analysis_result.get('final_score', 1.0)

            if abs(final_score) <= NEUTRAL_BIAS_THRESHOLD:
                neutral_articles_for_kb.append({"content": content, "url": url})
            else:
                biased_articles_for_review.append({"content": content, "url": url, "score": final_score})

        # Add neutral articles to Knowledge Base
        for article in neutral_articles_for_kb:
             kb.add_document(article["content"], article["url"])

        # Generate fact-checks
        fact_checks = []
        if kb.collection.count() > 0:
            for article in biased_articles_for_review:
                misconceptions = generate_misconceptions(article["content"])
                for misconception in misconceptions:
                    relevant_chunks = kb.query(misconception)
                    # # Note: generate_fact_check_report prints to console. 
                    # # For an API, this should be refactored to return JSON.
                    # # For now, we'll just log it.
                    # logger.info(f"Fact-checking misconception: '{misconception}'")
                    # fact_checks.append({
                    #     "misconception": misconception,
                    #     "source": article["url"],
                    #     "evidence_chunks": relevant_chunks
                    # })
                    report = generate_fact_check_report(misconception, relevant_chunks, article["url"])

                    # If a report was successfully generated, save it
                    if report:
                        report['misconception'] = misconception
                        report['biased_source'] = article["url"]
                        fact_checks.append(report)
        
        # Store final results
        job_results[job_id]["status"] = "complete"
        job_results[job_id]["results"] = {
            "summary": {
                "total_articles_analyzed": len(all_analyses),
                "neutral_articles_found": len(neutral_articles_for_kb),
                "biased_articles_found": len(biased_articles_for_review),
                "fact_checks_generated": len(fact_checks),
            },
            "analyses": all_analyses,
            "fact_checks": fact_checks
        }
        logger.info(f"Job {job_id}: Topic analysis completed successfully.")

    except Exception as e:
        logger.error(f"Job {job_id}: An error occurred during topic analysis: {e}")
        job_results[job_id]["status"] = "failed"
        job_results[job_id]["error"] = str(e)