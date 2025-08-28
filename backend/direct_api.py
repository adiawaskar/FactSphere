from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
import logging
import traceback
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("trends-api")

# Add the current directory to the path to import the utils module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the trends function
from utils.trends import get_trending_topics

# Import the lightweight agent service
try:
    from agents.misinformation_agent_lite import agent_service
    HAS_AGENT = True
    logger.info("Successfully imported enhanced lightweight agent_service")
    
    # Check if Gemini API is available
    HAS_GEMINI = hasattr(agent_service, '_analyze_with_gemini') and agent_service._analyze_with_gemini({}) != {}
    if HAS_GEMINI:
        logger.info("Gemini API integration is available")
    else:
        logger.info("Gemini API integration is not available - using basic analysis only")
        
except ImportError as e:
    logger.error(f"Failed to import lightweight agent: {str(e)}")
    logger.error("To fix dependency issues, run 'python install_dependencies.py'")
    HAS_AGENT = False
    HAS_GEMINI = False

# Agent analysis background task
is_agent_running = False
last_agent_run_time = None
agent_results = {
    "success": True,
    "timestamp": datetime.now().isoformat(),
    "message": "AI analysis not available. Please check dependencies or server logs.",
    "analysis": "The AI analysis module couldn't be loaded due to missing dependencies. Please run 'python install_dependencies.py' on the server.",
    "fallback": True,
    "error_details": "Dependencies may be missing. Check server logs for details."
}

app = FastAPI(title="FactSphere API", description="Misinformation Detection System API")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_risk_level(topic, articles):
    """Calculate misinformation risk level"""
    if topic is None:
        return "medium"  # Default risk level
        
    high_risk_keywords = ['hoax', 'conspiracy', 'fraud', 'fake', 'scam']
    medium_risk_keywords = ['claim', 'alleged', 'report', 'rumor']
    
    # Check topic for risk keywords
    if any(keyword in topic.lower() for keyword in high_risk_keywords):
        return "high"
    
    if any(keyword in topic.lower() for keyword in medium_risk_keywords):
        return "medium"
    
    return random.choice(["low", "medium", "high"])

def calculate_sentiment(topic, articles):
    """Safe sentiment analysis that handles None values"""
    positive_words = ['good', 'great', 'positive', 'breakthrough', 'success']
    negative_words = ['bad', 'negative', 'fail', 'problem', 'issue', 'controversy']
    
    positive_count = 0
    negative_count = 0
    
    # Safely check topic
    if topic:
        try:
            topic_lower = topic.lower()
            positive_count += sum(1 for word in positive_words if word in topic_lower)
            negative_count += sum(1 for word in negative_words if word in topic_lower)
        except (AttributeError, TypeError):
            pass
    
    # Safely check article content
    for article in articles:
        # Check title
        if 'title' in article and article['title']:
            try:
                title_lower = article['title'].lower()
                positive_count += sum(1 for word in positive_words if word in title_lower)
                negative_count += sum(1 for word in negative_words if word in title_lower)
            except (AttributeError, TypeError):
                logger.debug("Could not process article title")
        
        # Check snippet
        if 'snippet' in article and article['snippet']:
            try:
                snippet_lower = article['snippet'].lower()
                positive_count += sum(1 for word in positive_words if word in snippet_lower)
                negative_count += sum(1 for word in negative_words if word in snippet_lower)
            except (AttributeError, TypeError):
                logger.debug("Could not process article snippet")
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

async def run_agent_analysis():
    """Run the agent analysis in the background."""
    global is_agent_running, last_agent_run_time, agent_results
    
    if not HAS_AGENT:
        logger.error("No agent service available")
        is_agent_running = False
        return
    
    try:
        is_agent_running = True
        logger.info("Starting enhanced lightweight agent analysis...")
        
        # Run the lightweight agent analysis
        results = agent_service.analyze_trends()
        
        # Update global state
        agent_results = results
        last_agent_run_time = datetime.now().isoformat()
        logger.info("Enhanced lightweight agent analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error running enhanced lightweight agent analysis: {e}")
        logger.error(traceback.format_exc())
        
        # Update agent_results with error information
        error_message = str(e)
        agent_results = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "message": "Error during lightweight AI analysis",
            "analysis": "An error occurred while running the lightweight AI analysis. Please check the server logs for details.",
            "error_details": error_message,
            "using_lightweight_model": True
        }
    finally:
        is_agent_running = False

@app.get("/api/trends")
async def get_trends():
    try:
        logger.info("API request received for /api/trends")
        
        # Get trending topics
        trends_data = get_trending_topics()
        logger.info(f"Retrieved {len(trends_data)} trends from get_trending_topics()")
        
        # Format the response
        formatted_trends = []
        
        for trend in trends_data:
            try:
                topic = trend.get('topic', 'Unknown Topic')
                articles = trend.get('articles', [])
                
                # Get volume or estimate mentions
                mentions = trend.get('volume', random.randint(5000, 50000))
                
                # Calculate risk level and sentiment safely
                try:
                    risk_level = calculate_risk_level(topic, articles)
                except Exception as risk_error:
                    logger.warning(f"Error calculating risk level: {str(risk_error)}")
                    risk_level = "medium"  # Default
                    
                try:
                    sentiment = calculate_sentiment(topic, articles)
                except Exception as sentiment_error:
                    logger.warning(f"Error calculating sentiment: {str(sentiment_error)}")
                    sentiment = "neutral"  # Default
                
                # Generate a description from articles if available
                description = "No description available"
                if articles and len(articles) > 0:
                    if 'snippet' in articles[0] and articles[0]['snippet']:
                        description = articles[0]['snippet']
                    elif 'title' in articles[0] and articles[0]['title']:
                        description = articles[0]['title']
                
                # Format timestamp
                timestamp = "Recently"
                if 'started' in trend and trend['started']:
                    timestamp = trend['started']
                
                # Assign platform (in a real app, this would be determined from data source)
                platform = random.choice(['twitter', 'facebook', 'instagram', 'tiktok'])
                
                formatted_trend = {
                    "topic": topic,
                    "platform": platform,
                    "mentions": mentions,
                    "sentiment": sentiment,
                    "misinformationRisk": risk_level,
                    "description": description,
                    "timestamp": timestamp
                }
                
                formatted_trends.append(formatted_trend)
                logger.debug(f"Successfully processed trend: {topic}")
                
            except Exception as trend_error:
                logger.error(f"Error processing individual trend: {str(trend_error)}")
                logger.error(traceback.format_exc())
                # Skip this trend but continue processing others
        
        logger.info(f"Returning {len(formatted_trends)} formatted trends")
        return {
            "success": True,
            "trends": formatted_trends
        }
    
    except Exception as e:
        logger.error(f"Error in get_trends endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")

@app.get("/api/agent/status")
async def get_agent_status():
    """Get the current status of the agent."""
    return {
        "available": HAS_AGENT,
        "running": is_agent_running,
        "last_run": last_agent_run_time,
        "using_enhanced_analysis": True,
        "gemini_api_available": HAS_GEMINI
    }

@app.post("/api/agent/analyze")
async def trigger_agent_analysis(background_tasks: BackgroundTasks):
    """Trigger a new agent analysis."""
    global is_agent_running
    
    if not HAS_AGENT:
        return {
            "success": False,
            "message": "Agent service not available. Using fallback mode.",
            "fallback": True
        }
    
    if is_agent_running:
        return {
            "success": True,
            "message": "Agent analysis already running",
            "running": True
        }
    
    # Start the analysis in the background
    background_tasks.add_task(run_agent_analysis)
    
    return {
        "success": True,
        "message": "Enhanced lightweight agent analysis started",
        "using_gemini_api": HAS_GEMINI
    }

@app.get("/api/agent/results")
async def get_agent_results():
    """Get the latest agent analysis results."""
    global agent_results
    
    if not HAS_AGENT:
        # Return a fallback response if no agent module is available
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Agent service not available. Using fallback analysis.",
            "analysis": "The AI analysis module isn't available on this server. Only basic trend analysis is being used.",
            "fallback": True
        }
    
    try:
        # Try to load results from the agent service
        results = agent_service.get_latest_results()
        if results:
            agent_results = results
            return results
        
        # If no results are available, return a default response
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": "No analysis has been run yet. Please trigger an analysis first.",
            "analysis": "The AI agent hasn't analyzed any trends yet. Click 'Run AI Analysis' to start.",
            "using_enhanced_analysis": True
        }
    except Exception as e:
        logger.error(f"Error getting agent results: {e}")
        logger.error(traceback.format_exc())
        # Return a fallback response on error
        return {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Error retrieving agent results",
            "analysis": "There was an error retrieving the AI analysis. Please try again later."
        }

@app.get("/")
async def root():
    deps_status = "All dependencies installed" if HAS_AGENT else "Missing dependencies"
    api_status = "with Gemini API integration" if HAS_GEMINI else "with basic analysis only"
    
    return {
        "message": "Welcome to FactSphere API",
        "status": "Running",
        "agent_available": HAS_AGENT,
        "agent_type": f"Enhanced lightweight agent {api_status}",
        "dependencies": deps_status,
        "endpoints": [
            {"path": "/api/trends", "method": "GET", "description": "Get current trending topics"},
            {"path": "/api/agent/status", "method": "GET", "description": "Check agent status"},
            {"path": "/api/agent/results", "method": "GET", "description": "Get agent analysis results"},
            {"path": "/api/agent/analyze", "method": "POST", "description": "Trigger an enhanced lightweight agent analysis"}
        ]
    }

if __name__ == "__main__":
    logger.info("Starting the FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
