# backend/api/bias_routes.py
import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

# --- Add project root to system path ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# ---

from backend.services.bias_service import analyze_single_url, run_topic_analysis_background, job_results

logger = logging.getLogger("bias_routes")
router = APIRouter()

class AnalyzeUrlRequest(BaseModel):
    url: str

class AnalyzeTopicRequest(BaseModel):
    topic: str

@router.post("/bias/analyze-url")
async def analyze_url_endpoint(request: AnalyzeUrlRequest):
    """
    Synchronously analyzes a single URL for bias.
    """
    if not request.url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
    
    result = analyze_single_url(request.url)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("message", "Analysis failed."))
        
    return result

@router.post("/bias/analyze-topic")
async def analyze_topic_endpoint(request: AnalyzeTopicRequest, background_tasks: BackgroundTasks):
    """
    Starts a background task to analyze a topic for bias.
    Returns a job ID for polling results.
    """
    if not request.topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    job_id = str(uuid.uuid4())
    background_tasks.add_task(run_topic_analysis_background, job_id, request.topic)
    
    return {"success": True, "message": "Topic analysis started.", "job_id": job_id}

@router.get("/bias/results/{job_id}")
async def get_analysis_results(job_id: str):
    """
    Retrieves the status and results of a background analysis job.
    """
    job = job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    
    return {"success": True, "job_id": job_id, "data": job}