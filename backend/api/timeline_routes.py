# backend/api/timeline_routes.py
import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.services.timeline_service import run_timeline_generation_background, timeline_job_results

logger = logging.getLogger("timeline_routes")
router = APIRouter()

class GenerateTimelineRequest(BaseModel):
    topic: str

@router.post("/timeline/generate")
async def generate_timeline_endpoint(request: GenerateTimelineRequest, background_tasks: BackgroundTasks):
    """
    Starts a background task to generate a news timeline for a topic.
    """
    if not request.topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    job_id = str(uuid.uuid4())
    background_tasks.add_task(run_timeline_generation_background, job_id, request.topic)
    
    return {"success": True, "message": "Timeline generation started.", "job_id": job_id}

@router.get("/timeline/results/{job_id}")
async def get_timeline_results(job_id: str):
    """
    Retrieves the status and results of a background timeline generation job.
    """
    job = timeline_job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    
    # Unlike the bias agent, the results are not nested in a 'data' key.
    # We return the whole job object for consistency with the bias agent's response structure on the frontend.
    return {"success": True, "job_id": job_id, "data": job}