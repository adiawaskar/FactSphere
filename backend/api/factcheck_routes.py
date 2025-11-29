# from fastapi import APIRouter, HTTPException, Request, Body
# from pydantic import BaseModel
# from typing import Optional, Dict, Any
# import uuid
# import json
# import sys, os

# # Fix Python path
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, PROJECT_ROOT)

# # Import pipeline
# from backend.agents.fact_judge_jury import fact_check_pipeline

# router = APIRouter()

# # Schema for Swagger only
# class FactCheckRequest(BaseModel):
#     message: str
#     run_id: Optional[str] = None


# @router.post(
#     "/factcheck",
#     response_model=Dict[str, Any],
#     summary="Run full fact-check pipeline",
#     description="Accepts JSON {message: text} or raw text/plain input."
# )
# async def run_factcheck(
#     request: Request,
#     body: Optional[FactCheckRequest] = Body(
#         default=None,
#         description="Message to fact-check (JSON only; raw text also supported)."
#     )
# ):
#     """
#     Accept BOTH:
#       - JSON body:  { "message": "..." }
#       - Raw text/plain: "...."
#     """

#     content_type = request.headers.get("content-type", "").lower()

#     # CASE 1 — raw text/plain
#     if "text/plain" in content_type:
#         raw = (await request.body()).decode("utf-8")
#         message = raw.strip()
#         run_id = str(uuid.uuid4())

#     # CASE 2 — JSON
#     elif "application/json" in content_type:
#         if body is None:
#             raise HTTPException(status_code=400, detail="Invalid JSON")
#         message = body.message.strip()
#         run_id = body.run_id or str(uuid.uuid4())

#     else:
#         raise HTTPException(status_code=400, detail="Unsupported content type")

#     if not message:
#         raise HTTPException(status_code=400, detail="Message cannot be empty")

#     # run the real pipeline
#     try:
#         result = fact_check_pipeline(message)
#         return {
#             "success": True,
#             "run_id": run_id,
#             "result": result
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "run_id": run_id,
#             "error": str(e)
#         }
from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import json
import sys, os

# Fix Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from backend.agents.bias_analyzer_priyank.config import CONSOLE, GEMINI_API_KEY, LLM_FAST_MODEL, LLM_SMART_MODEL

# Import pipeline
from backend.agents.fact_judge_jury import fact_check_pipeline

router = APIRouter()

# Schema for Swagger only
class FactCheckRequest(BaseModel):
    message: str
    run_id: Optional[str] = None


# @router.post(
#     "/factcheck",
#     response_model=Dict[str, Any],
#     summary="Run full fact-check pipeline",
#     description="Accepts JSON {message: text} or raw text/plain input."
# )
# async def run_factcheck(
#     request: Request,
#     body: Optional[FactCheckRequest] = Body(
#         default=None,
#         description="Message to fact-check (JSON only; raw text also supported)."
#     )
# ):
#     """
#     Accept BOTH:
#       - JSON body:  { "message": "..." }
#       - Raw text/plain: "...."
#     """

#     content_type = request.headers.get("content-type", "").lower()
#     message = None
#     run_id = None

#     # CASE 1 — raw text/plain
#     if "text/plain" in content_type:
#         raw_body = await request.body()
#         message = raw_body.decode("utf-8").strip()
#         run_id = str(uuid.uuid4())

#     # CASE 2 — JSON
#     elif "application/json" in content_type:
#         # Don't try to read the body again - FastAPI already parsed it into the 'body' parameter
#         if body is None:
#             # If body is None but content-type is JSON, try to parse manually as fallback
#             try:
#                 raw_body = await request.body()
#                 json_data = json.loads(raw_body)
#                 message = json_data.get("message", "").strip()
#                 run_id = json_data.get("run_id") or str(uuid.uuid4())
#             except json.JSONDecodeError:
#                 raise HTTPException(status_code=400, detail="Invalid JSON")
#         else:
#             message = body.message.strip()
#             run_id = body.run_id or str(uuid.uuid4())

#     else:
#         raise HTTPException(status_code=400, detail="Unsupported content type")

#     if not message:
#         raise HTTPException(status_code=400, detail="Message cannot be empty")

#     # run the real pipeline
#     try:
#         result = fact_check_pipeline(message)
#         return {
#             "success": True,
#             "run_id": run_id,
#             "result": result
#         }
#     except Exception as e:
#         return {
#             "success": False,
#             "run_id": run_id,
#             "error": str(e)
#         }
@router.post("/factcheck")
async def run_factcheck(
    request: Request,
    body: Optional[FactCheckRequest] = Body(default=None)
):
    content_type = request.headers.get("content-type", "").lower()
    message = None
    run_id = None

    # CASE 1 — raw text/plain
    if "text/plain" in content_type:
        raw_body = await request.body()
        message = raw_body.decode("utf-8").strip()
        run_id = str(uuid.uuid4())

    # CASE 2 — JSON
    elif "application/json" in content_type:
        if body is None:
            try:
                raw_body = await request.body()
                json_data = json.loads(raw_body)
                message = json_data.get("message", "").strip()
                run_id = json_data.get("run_id") or str(uuid.uuid4())
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
        else:
            message = body.message.strip()
            run_id = body.run_id or str(uuid.uuid4())

    else:
        raise HTTPException(status_code=400, detail="Unsupported content type")

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Run the pipeline with better error handling
    try:
        result = fact_check_pipeline(message)
        
        # Validate that result is JSON-serializable
        try:
            json.dumps(result)  # Test serialization
        except (TypeError, ValueError) as e:
            CONSOLE.print(f"[red]JSON serialization error: {e}[/red]")
            # Return a simplified, serializable version
            return {
                "success": True,
                "run_id": run_id,
                "result": {
                    "input_message": result.get("input_message", message),
                    "comprehensive_verdict": result.get("comprehensive_verdict", {}),
                    "timestamp": result.get("timestamp", ""),
                    "error": "Some data could not be serialized"
                }
            }
        
        return {
            "success": True,
            "run_id": run_id,
            "result": result
        }
        
    except Exception as e:
        CONSOLE.print(f"[red]Pipeline error: {e}[/red]")
        return {
            "success": False,
            "run_id": run_id,
            "error": str(e)
        }