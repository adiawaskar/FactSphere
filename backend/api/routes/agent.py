from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-api")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the agent service
try:
    from agents.misinformation_agent_lite import agent_service
    HAS_AGENT = True
except ImportError:
    logger.error("Could not import misinformation agent")
    HAS_AGENT = False

router = APIRouter(prefix="/agent", tags=["agent"])

# Track whether analysis is currently running
is_analysis_running = False
last_analysis_time = None

@router.get("/status")
async def get_agent_status() -> Dict[str, Any]:
    """Get the status of the misinformation agent."""
    global last_analysis_time
    
    return {
        "available": HAS_AGENT,
        "running": is_analysis_running,
        "last_run": last_analysis_time,
        "gemini_api_available": HAS_AGENT and agent_service.HAS_GEMINI_API if HAS_AGENT else False
    }

@router.post("/analyze")
async def start_analysis(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start a new analysis of global misinformation trends in the background."""
    global is_analysis_running
    
    if not HAS_AGENT:
        raise HTTPException(
            status_code=503, 
            detail="Misinformation agent is not available"
        )
    
    if is_analysis_running:
        return {
            "success": False,
            "message": "Analysis is already running"
        }
    
    # Define the background task
    def run_analysis():
        global is_analysis_running, last_analysis_time
        try:
            is_analysis_running = True
            agent_service.analyze_trends()
            last_analysis_time = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error running analysis: {str(e)}")
        finally:
            is_analysis_running = False
    
    # Add the task to be run in the background
    background_tasks.add_task(run_analysis)
    
    return {
        "success": True,
        "message": "Analysis started in the background"
    }

@router.get("/results")
async def get_analysis_results() -> Dict[str, Any]:
    """Get the latest analysis results from the misinformation agent."""
    if not HAS_AGENT:
        raise HTTPException(
            status_code=503, 
            detail="Misinformation agent is not available"
        )
    
    results = agent_service.get_latest_results()
    return results
