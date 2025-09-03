from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.trend_routes import router as trends_router
from backend.api import analyze

app = FastAPI(title="FactSphere API", description="Misinformation Detection System API")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[        "http://localhost:8080",  # your frontend
"http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the trends router
app.include_router(trends_router)
app.include_router(analyze.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to FactSphere API"}
