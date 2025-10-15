import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("render-app")

# Print debugging information
port = int(os.environ.get("PORT", 10000))
logger.info(f"PORT environment variable: {os.environ.get('PORT')}")
logger.info(f"Starting server on port {port}")
print(f"STARTUP: Using port {port}")

# Make sure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run app
try:
    import uvicorn
    logger.info("Imported uvicorn successfully")
    print("Starting Uvicorn server...")
    
    # Run with direct command - better for Render
    if __name__ == "__main__":
        uvicorn.run("backend.direct_api:app", host="0.0.0.0", port=port, log_level="info")
except Exception as e:
    logger.error(f"Error starting server: {e}")
    print(f"ERROR: Failed to start server: {e}")
    raise