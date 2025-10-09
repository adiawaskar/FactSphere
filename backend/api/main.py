#backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Import routers
from backend.api.trend_routes import router as trends_router
from backend.api import analyze

app = FastAPI(
    title="FactSphere API",
    description="API for misinformation detection and trend analysis",
    version="1.0.0"
)

# Configure CORS to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trends_router)
app.include_router(analyze.router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "FactSphere API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "trends": "/api/trends",
            "analysis": "/api/analysis",
            "agent": "/api/agent"
        }
    }

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Internal server error: {str(exc)}"}
    )

# Mount static files if available
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted from {static_dir}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
