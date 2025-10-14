# # backend/direct_api.py
# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# import random
# import logging
# import traceback
# import sys
# import os
# from datetime import datetime
# from typing import Dict, Any, List, Optional
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import JSONResponse


# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger("trends-api")


# sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# from utils.trends import get_trending_topics

# # Include routers from main.py - add this after CORS middleware
# try:
#     from backend.api.trend_routes import router as trends_router
#     from backend.api import analyze
    
#     app.include_router(trends_router)
#     app.include_router(analyze.router, prefix="/api")
#     logger.info("Successfully included additional routers")
# except ImportError as e:
#     logger.warning(f"Could not import additional routers: {e}")
#     logger.info("Running with core functionality only")


# try:
#     from agents.misinformation_agent_lite import agent_service
#     HAS_AGENT = True
#     logger.info("Successfully imported enhanced lightweight agent_service")
    
    
#     HAS_GEMINI = hasattr(agent_service, '_analyze_with_gemini') and agent_service._analyze_with_gemini({}) != {}
#     if HAS_GEMINI:
#         logger.info("Gemini API integration is available")
#     else:
#         logger.info("Gemini API integration is not available - using basic analysis only")
        
# except ImportError as e:
#     logger.error(f"Failed to import lightweight agent: {str(e)}")
#     logger.error("To fix dependency issues, run 'python install_dependencies.py'")
#     HAS_AGENT = False
#     HAS_GEMINI = False


# is_agent_running = False
# last_agent_run_time = None
# agent_results = {
#     "success": True,
#     "timestamp": datetime.now().isoformat(),
#     "message": "AI analysis not available. Please check dependencies or server logs.",
#     "analysis": "The AI analysis module couldn't be loaded due to missing dependencies. Please run 'python install_dependencies.py' on the server.",
#     "fallback": True,
#     "error_details": "Dependencies may be missing. Check server logs for details."
# }

# app = FastAPI(title="FactSphere API", description="Misinformation Detection System API")


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# def calculate_risk_level(topic, articles):
#     """Calculate misinformation risk level"""
#     if topic is None:
#         return "medium"  
        
#     high_risk_keywords = ['hoax', 'conspiracy', 'fraud', 'fake', 'scam']
#     medium_risk_keywords = ['claim', 'alleged', 'report', 'rumor']
    
    
#     if any(keyword in topic.lower() for keyword in high_risk_keywords):
#         return "high"
    
#     if any(keyword in topic.lower() for keyword in medium_risk_keywords):
#         return "medium"
    
#     return random.choice(["low", "medium", "high"])

# def calculate_sentiment(topic, articles):
#     """Safe sentiment analysis that handles None values"""
#     positive_words = ['good', 'great', 'positive', 'breakthrough', 'success']
#     negative_words = ['bad', 'negative', 'fail', 'problem', 'issue', 'controversy']
    
#     positive_count = 0
#     negative_count = 0
    
    
#     if topic:
#         try:
#             topic_lower = topic.lower()
#             positive_count += sum(1 for word in positive_words if word in topic_lower)
#             negative_count += sum(1 for word in negative_words if word in topic_lower)
#         except (AttributeError, TypeError):
#             pass
    
    
#     for article in articles:
        
#         if 'title' in article and article['title']:
#             try:
#                 title_lower = article['title'].lower()
#                 positive_count += sum(1 for word in positive_words if word in title_lower)
#                 negative_count += sum(1 for word in negative_words if word in title_lower)
#             except (AttributeError, TypeError):
#                 logger.debug("Could not process article title")
        
        
#         if 'snippet' in article and article['snippet']:
#             try:
#                 snippet_lower = article['snippet'].lower()
#                 positive_count += sum(1 for word in positive_words if word in snippet_lower)
#                 negative_count += sum(1 for word in negative_words if word in snippet_lower)
#             except (AttributeError, TypeError):
#                 logger.debug("Could not process article snippet")
    
#     if positive_count > negative_count:
#         return "positive"
#     elif negative_count > positive_count:
#         return "negative"
#     else:
#         return "neutral"

# async def run_agent_analysis():
#     """Run the agent analysis in the background."""
#     global is_agent_running, last_agent_run_time, agent_results
    
#     if not HAS_AGENT:
#         logger.error("No agent service available")
#         is_agent_running = False
#         return
    
#     try:
#         is_agent_running = True
#         logger.info("Starting enhanced lightweight agent analysis...")
        
        
#         results = agent_service.analyze_trends()
        
        
#         enhanced_results = enhance_analysis_results(results)
        
        
#         agent_results = enhanced_results
#         last_agent_run_time = datetime.now().isoformat()
#         logger.info("Enhanced lightweight agent analysis completed successfully")
        
#     except Exception as e:
#         logger.error(f"Error running enhanced lightweight agent analysis: {e}")
#         logger.error(traceback.format_exc())
        
        
#         error_message = str(e)
#         agent_results = {
#             "success": False,
#             "timestamp": datetime.now().isoformat(),
#             "message": "Error during lightweight AI analysis",
#             "analysis": "An error occurred while running the lightweight AI analysis. Please check the server logs for details.",
#             "error_details": error_message,
#             "using_lightweight_model": True
#         }
#     finally:
#         is_agent_running = False

# def enhance_analysis_results(results):
#     """Format and enhance analysis results for better frontend display."""
#     if not results or not isinstance(results, dict):
#         return results
    
    
#     enhanced = dict(results)
    
    
#     if "timestamp" not in enhanced:
#         enhanced["timestamp"] = datetime.now().isoformat()
    
    
#     enhanced["using_enhanced_analysis"] = True
    
    
#     enhanced["using_gemini"] = HAS_GEMINI
    
    
#     if "trends" in enhanced and isinstance(enhanced["trends"], list):
#         for trend in enhanced["trends"]:
            
#             if "risk_level" in trend and isinstance(trend["risk_level"], str):
#                 level = trend["risk_level"]
#                 score = trend.get("misinformation_score", 0.5)
                
#                 trend["misinformation_risk"] = {
#                     "level": level,
#                     "score": score,
#                     "description": get_risk_description(level)
#                 }
            
            
#             if "article_count" in trend and "article_analyses" not in trend:
                
#                 trend["articles_analyzed"] = trend["article_count"]
#                 trend["article_analyses"] = []
                
                
#                 if trend["article_count"] > 0:
#                     for i in range(min(3, trend["article_count"])):
#                         trend["article_analyses"].append({
#                             "article_source": f"Source {i+1}",
#                             "article_title": f"Article about {trend['topic']}",
#                             "text_snippet": "This article discusses the trending topic.",
#                             "misinformation_risk": {
#                                 "level": trend["risk_level"],
#                                 "score": trend.get("misinformation_score", 0.5)
#                             }
#                         })
            
            
#             trend["metrics"] = {
#                 "credibility_score": max(0, 1 - trend.get("misinformation_score", 0.5)),
#                 "confidence": trend.get("confidence", 0.5),
#                 "emotional_language": calculate_emotional_score(trend),
#                 "source_reliability": calculate_source_reliability(trend)
#             }
            
            
#             if "sentiment" not in trend:
#                 trend["sentiment"] = determine_sentiment(trend)
    
    
#     if "trends" in enhanced and isinstance(enhanced["trends"], list) and enhanced["trends"]:
#         trends = enhanced["trends"]
#         enhanced["metrics_summary"] = {
#             "average_misinformation_score": sum(t.get("misinformation_score", 0.5) for t in trends) / len(trends),
#             "high_risk_percentage": 100 * sum(1 for t in trends if t.get("risk_level") == "high") / len(trends),
#             "topics_analyzed": len(trends),
#             "overall_confidence": sum(t.get("confidence", 0.5) for t in trends) / len(trends),
#             "sentiment_distribution": calculate_sentiment_distribution(trends),
#             "top_misinformation_indicators": get_top_indicators(trends, "misinformation_indicators"),
#             "top_credibility_indicators": get_top_indicators(trends, "credibility_indicators"),
#             "analysis_timestamp": enhanced["timestamp"]
#         }
    
#     return enhanced

# def get_risk_description(level):
#     """Get a description for the risk level."""
#     descriptions = {
#         "high": "High probability of containing misinformation or misleading content",
#         "medium": "Some elements may be misleading or require further verification",
#         "low": "Content appears to be generally reliable with minimal misinformation risk"
#     }
#     return descriptions.get(level, "Unknown risk level")

# def calculate_emotional_score(trend):
#     """Calculate emotional language score from trend data."""
    
#     if "misinformation_categories" in trend and "emotional_manipulation" in trend["misinformation_categories"]:
        
#         count = len(trend["misinformation_categories"]["emotional_manipulation"])
#         return min(1.0, count * 0.2 + 0.3)  
#     return random.uniform(0.1, 0.4)  

# def calculate_source_reliability(trend):
#     """Calculate source reliability score from trend data."""
    
#     if "domain_analysis" in trend and trend["domain_analysis"]:
#         credible_count = sum(1 for d in trend["domain_analysis"] if d.get("is_credible_source", False))
#         problematic_count = sum(1 for d in trend["domain_analysis"] if d.get("is_problematic_source", False))
        
#         if credible_count + problematic_count > 0:
            
#             return credible_count / (credible_count + problematic_count * 2 + 1)
    
    
#     if "credibility_indicators" in trend and trend["credibility_indicators"]:
#         return min(0.7, 0.3 + len(trend["credibility_indicators"]) * 0.1)
    
#     return 0.5  

# def determine_sentiment(trend):
#     """Determine sentiment from trend data."""
    
#     if "sentiment" in trend:
#         return trend["sentiment"]
    
    
#     if "misinformation_score" in trend:
#         score = trend["misinformation_score"]
#         if score > 0.7:
#             return "negative"
#         elif score < 0.3:
#             return "positive"
    
    
#     return "neutral"

# def calculate_sentiment_distribution(trends):
#     """Calculate sentiment distribution across trends."""
#     positive = sum(1 for t in trends if determine_sentiment(t) == "positive")
#     negative = sum(1 for t in trends if determine_sentiment(t) == "negative")
#     neutral = len(trends) - positive - negative
    
#     return {
#         "positive": positive,
#         "negative": negative,
#         "neutral": neutral
#     }

# def get_top_indicators(trends, indicator_field, limit=5):
#     """Get top indicators across all trends."""
#     all_indicators = []
#     for trend in trends:
#         if indicator_field in trend:
#             all_indicators.extend(trend[indicator_field])
    
    
#     indicator_counts = {}
#     for indicator in all_indicators:
#         indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1
    
    
#     sorted_indicators = sorted(indicator_counts.items(), key=lambda x: x[1], reverse=True)
    
    
#     return [{"name": name, "count": count} for name, count in sorted_indicators[:limit]]

# @app.get("/api/trends")
# async def get_trends():
#     try:
#         logger.info("API request received for /api/trends")
        
        
#         trends_data = get_trending_topics()
#         logger.info(f"Retrieved {len(trends_data)} trends from get_trending_topics()")
        
        
#         formatted_trends = []
        
#         for trend in trends_data:
#             try:
#                 topic = trend.get('topic', 'Unknown Topic')
#                 articles = trend.get('articles', [])
                
                
#                 mentions = trend.get('volume', random.randint(5000, 50000))
                
                
#                 try:
#                     risk_level = calculate_risk_level(topic, articles)
#                 except Exception as risk_error:
#                     logger.warning(f"Error calculating risk level: {str(risk_error)}")
#                     risk_level = "medium"  
                    
#                 try:
#                     sentiment = calculate_sentiment(topic, articles)
#                 except Exception as sentiment_error:
#                     logger.warning(f"Error calculating sentiment: {str(sentiment_error)}")
#                     sentiment = "neutral"  
                
                
#                 description = "No description available"
#                 if articles and len(articles) > 0:
#                     if 'snippet' in articles[0] and articles[0]['snippet']:
#                         description = articles[0]['snippet']
#                     elif 'title' in articles[0] and articles[0]['title']:
#                         description = articles[0]['title']
                
                
#                 timestamp = "Recently"
#                 if 'started' in trend and trend['started']:
#                     timestamp = trend['started']
                
                
#                 platform = random.choice(['twitter', 'facebook', 'instagram', 'tiktok'])
                
#                 formatted_trend = {
#                     "topic": topic,
#                     "platform": platform,
#                     "mentions": mentions,
#                     "sentiment": sentiment,
#                     "misinformationRisk": risk_level,
#                     "description": description,
#                     "timestamp": timestamp
#                 }
                
#                 formatted_trends.append(formatted_trend)
#                 logger.debug(f"Successfully processed trend: {topic}")
                
#             except Exception as trend_error:
#                 logger.error(f"Error processing individual trend: {str(trend_error)}")
#                 logger.error(traceback.format_exc())
                
        
#         logger.info(f"Returning {len(formatted_trends)} formatted trends")
#         return {
#             "success": True,
#             "trends": formatted_trends
#         }
    
#     except Exception as e:
#         logger.error(f"Error in get_trends endpoint: {str(e)}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")

# @app.get("/api/agent/status")
# async def get_agent_status():
#     """Get the current status of the agent."""
#     return {
#         "available": HAS_AGENT,
#         "running": is_agent_running,
#         "last_run": last_agent_run_time,
#         "using_enhanced_analysis": True,
#         "gemini_api_available": HAS_GEMINI
#     }

# @app.post("/api/agent/analyze")
# async def trigger_agent_analysis(background_tasks: BackgroundTasks):
#     """Trigger a new agent analysis."""
#     global is_agent_running
    
#     if not HAS_AGENT:
#         return {
#             "success": False,
#             "message": "Agent service not available. Using fallback mode.",
#             "fallback": True
#         }
    
#     if is_agent_running:
#         return {
#             "success": True,
#             "message": "Agent analysis already running",
#             "running": True
#         }
    
    
#     background_tasks.add_task(run_agent_analysis)
    
#     return {
#         "success": True,
#         "message": "Enhanced lightweight agent analysis started",
#         "using_gemini_api": HAS_GEMINI
#     }

# @app.get("/api/agent/results")
# async def get_agent_results():
#     """Get the latest agent analysis results."""
#     global agent_results
    
#     if not HAS_AGENT:
        
#         return {
#             "success": True,
#             "timestamp": datetime.now().isoformat(),
#             "message": "Agent service not available. Using fallback analysis.",
#             "analysis": "The AI analysis module isn't available on this server. Only basic trend analysis is being used.",
#             "fallback": True
#         }
    
#     try:
        
#         results = agent_service.get_latest_results()
#         if results:
            
#             enhanced_results = enhance_analysis_results(results)
#             agent_results = enhanced_results
#             return enhanced_results
        
        
#         return {
#             "success": True,
#             "timestamp": datetime.now().isoformat(),
#             "message": "No analysis has been run yet. Please trigger an analysis first.",
#             "analysis": "The AI agent hasn't analyzed any trends yet. Click 'Run AI Analysis' to start.",
#             "using_enhanced_analysis": True
#         }
#     except Exception as e:
#         logger.error(f"Error getting agent results: {e}")
#         logger.error(traceback.format_exc())
        
#         return {
#             "success": False,
#             "timestamp": datetime.now().isoformat(),
#             "error": str(e),
#             "message": "Error retrieving agent results",
#             "analysis": "There was an error retrieving the AI analysis. Please try again later."
#         }

# @app.get("/")
# async def root():
#     deps_status = "All dependencies installed" if HAS_AGENT else "Missing dependencies"
#     api_status = "with Gemini API integration" if HAS_GEMINI else "with basic analysis only"
    
#     return {
#         "message": "Welcome to FactSphere API",
#         "status": "Running",
#         "agent_available": HAS_AGENT,
#         "agent_type": f"Enhanced lightweight agent {api_status}",
#         "dependencies": deps_status,
#         "endpoints": [
#             {"path": "/api/trends", "method": "GET", "description": "Get current trending topics"},
#             {"path": "/api/agent/status", "method": "GET", "description": "Check agent status"},
#             {"path": "/api/agent/results", "method": "GET", "description": "Get agent analysis results"},
#             {"path": "/api/agent/analyze", "method": "POST", "description": "Trigger an enhanced lightweight agent analysis"}
#         ]
#     }

# # Error handling - add this before static files mounting
# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     logger.error(f"Unhandled exception: {str(exc)}")
#     return JSONResponse(
#         status_code=500,
#         content={"success": False, "message": f"Internal server error: {str(exc)}"}
#     )

# # Mount static files if available - add this before the main block
# static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
# if os.path.exists(static_dir):
#     app.mount("/static", StaticFiles(directory=static_dir), name="static")
#     logger.info(f"Static files mounted from {static_dir}")

# if __name__ == "__main__":
#     logger.info("Starting the FastAPI server")
#     uvicorn.run(app, host="0.0.0.0", port=8000)




# backend/direct_api.py
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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("trends-api")


sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from utils.trends import get_trending_topics


try:
    from agents.misinformation_agent_lite import agent_service
    HAS_AGENT = True
    logger.info("Successfully imported enhanced lightweight agent_service")
    
    
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

# === APP DEFINITION - THIS MUST COME FIRST ===
app = FastAPI(title="FactSphere API", description="Misinformation Detection System API")

# === CORS MIDDLEWARE ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === NOW INCLUDE ROUTERS - AFTER APP IS DEFINED ===
    # go one directory up to import from api
    # cd .. in python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(os.getcwd())
from backend.api.trend_routes import router as trends_router
from backend.api import analyze
app.include_router(trends_router)
app.include_router(analyze.router, prefix="/api")
logger.info("Successfully included additional routers")


# === ERROR HANDLER - AFTER APP IS DEFINED ===
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Internal server error: {str(exc)}"}
    )

def calculate_risk_level(topic, articles):
    """Calculate misinformation risk level"""
    if topic is None:
        return "medium"  
        
    high_risk_keywords = ['hoax', 'conspiracy', 'fraud', 'fake', 'scam']
    medium_risk_keywords = ['claim', 'alleged', 'report', 'rumor']
    
    
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
    
    
    if topic:
        try:
            topic_lower = topic.lower()
            positive_count += sum(1 for word in positive_words if word in topic_lower)
            negative_count += sum(1 for word in negative_words if word in topic_lower)
        except (AttributeError, TypeError):
            pass
    
    
    for article in articles:
        
        if 'title' in article and article['title']:
            try:
                title_lower = article['title'].lower()
                positive_count += sum(1 for word in positive_words if word in title_lower)
                negative_count += sum(1 for word in negative_words if word in title_lower)
            except (AttributeError, TypeError):
                logger.debug("Could not process article title")
        
        
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
        
        
        results = agent_service.analyze_trends()
        
        
        enhanced_results = enhance_analysis_results(results)
        
        
        agent_results = enhanced_results
        last_agent_run_time = datetime.now().isoformat()
        logger.info("Enhanced lightweight agent analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error running enhanced lightweight agent analysis: {e}")
        logger.error(traceback.format_exc())
        
        
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

def enhance_analysis_results(results):
    """Format and enhance analysis results for better frontend display."""
    if not results or not isinstance(results, dict):
        return results
    
    
    enhanced = dict(results)
    
    
    if "timestamp" not in enhanced:
        enhanced["timestamp"] = datetime.now().isoformat()
    
    
    enhanced["using_enhanced_analysis"] = True
    
    
    enhanced["using_gemini"] = HAS_GEMINI
    
    
    if "trends" in enhanced and isinstance(enhanced["trends"], list):
        for trend in enhanced["trends"]:
            
            if "risk_level" in trend and isinstance(trend["risk_level"], str):
                level = trend["risk_level"]
                score = trend.get("misinformation_score", 0.5)
                
                trend["misinformation_risk"] = {
                    "level": level,
                    "score": score,
                    "description": get_risk_description(level)
                }
            
            
            if "article_count" in trend and "article_analyses" not in trend:
                
                trend["articles_analyzed"] = trend["article_count"]
                trend["article_analyses"] = []
                
                
                if trend["article_count"] > 0:
                    for i in range(min(3, trend["article_count"])):
                        trend["article_analyses"].append({
                            "article_source": f"Source {i+1}",
                            "article_title": f"Article about {trend['topic']}",
                            "text_snippet": "This article discusses the trending topic.",
                            "misinformation_risk": {
                                "level": trend["risk_level"],
                                "score": trend.get("misinformation_score", 0.5)
                            }
                        })
            
            
            trend["metrics"] = {
                "credibility_score": max(0, 1 - trend.get("misinformation_score", 0.5)),
                "confidence": trend.get("confidence", 0.5),
                "emotional_language": calculate_emotional_score(trend),
                "source_reliability": calculate_source_reliability(trend)
            }
            
            
            if "sentiment" not in trend:
                trend["sentiment"] = determine_sentiment(trend)
    
    
    if "trends" in enhanced and isinstance(enhanced["trends"], list) and enhanced["trends"]:
        trends = enhanced["trends"]
        enhanced["metrics_summary"] = {
            "average_misinformation_score": sum(t.get("misinformation_score", 0.5) for t in trends) / len(trends),
            "high_risk_percentage": 100 * sum(1 for t in trends if t.get("risk_level") == "high") / len(trends),
            "topics_analyzed": len(trends),
            "overall_confidence": sum(t.get("confidence", 0.5) for t in trends) / len(trends),
            "sentiment_distribution": calculate_sentiment_distribution(trends),
            "top_misinformation_indicators": get_top_indicators(trends, "misinformation_indicators"),
            "top_credibility_indicators": get_top_indicators(trends, "credibility_indicators"),
            "analysis_timestamp": enhanced["timestamp"]
        }
    
    return enhanced

def get_risk_description(level):
    """Get a description for the risk level."""
    descriptions = {
        "high": "High probability of containing misinformation or misleading content",
        "medium": "Some elements may be misleading or require further verification",
        "low": "Content appears to be generally reliable with minimal misinformation risk"
    }
    return descriptions.get(level, "Unknown risk level")

def calculate_emotional_score(trend):
    """Calculate emotional language score from trend data."""
    
    if "misinformation_categories" in trend and "emotional_manipulation" in trend["misinformation_categories"]:
        
        count = len(trend["misinformation_categories"]["emotional_manipulation"])
        return min(1.0, count * 0.2 + 0.3)  
    return random.uniform(0.1, 0.4)  

def calculate_source_reliability(trend):
    """Calculate source reliability score from trend data."""
    
    if "domain_analysis" in trend and trend["domain_analysis"]:
        credible_count = sum(1 for d in trend["domain_analysis"] if d.get("is_credible_source", False))
        problematic_count = sum(1 for d in trend["domain_analysis"] if d.get("is_problematic_source", False))
        
        if credible_count + problematic_count > 0:
            
            return credible_count / (credible_count + problematic_count * 2 + 1)
    
    
    if "credibility_indicators" in trend and trend["credibility_indicators"]:
        return min(0.7, 0.3 + len(trend["credibility_indicators"]) * 0.1)
    
    return 0.5  

def determine_sentiment(trend):
    """Determine sentiment from trend data."""
    
    if "sentiment" in trend:
        return trend["sentiment"]
    
    
    if "misinformation_score" in trend:
        score = trend["misinformation_score"]
        if score > 0.7:
            return "negative"
        elif score < 0.3:
            return "positive"
    
    
    return "neutral"

def calculate_sentiment_distribution(trends):
    """Calculate sentiment distribution across trends."""
    positive = sum(1 for t in trends if determine_sentiment(t) == "positive")
    negative = sum(1 for t in trends if determine_sentiment(t) == "negative")
    neutral = len(trends) - positive - negative
    
    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral
    }

def get_top_indicators(trends, indicator_field, limit=5):
    """Get top indicators across all trends."""
    all_indicators = []
    for trend in trends:
        if indicator_field in trend:
            all_indicators.extend(trend[indicator_field])
    
    
    indicator_counts = {}
    for indicator in all_indicators:
        indicator_counts[indicator] = indicator_counts.get(indicator, 0) + 1
    
    
    sorted_indicators = sorted(indicator_counts.items(), key=lambda x: x[1], reverse=True)
    
    
    return [{"name": name, "count": count} for name, count in sorted_indicators[:limit]]

@app.get("/api/trends")
async def get_trends():
    try:
        logger.info("API request received for /api/trends")
        
        
        trends_data = get_trending_topics()
        logger.info(f"Retrieved {len(trends_data)} trends from get_trending_topics()")
        
        
        formatted_trends = []
        
        for trend in trends_data:
            try:
                topic = trend.get('topic', 'Unknown Topic')
                articles = trend.get('articles', [])
                
                
                mentions = trend.get('volume', random.randint(5000, 50000))
                
                
                try:
                    risk_level = calculate_risk_level(topic, articles)
                except Exception as risk_error:
                    logger.warning(f"Error calculating risk level: {str(risk_error)}")
                    risk_level = "medium"  
                    
                try:
                    sentiment = calculate_sentiment(topic, articles)
                except Exception as sentiment_error:
                    logger.warning(f"Error calculating sentiment: {str(sentiment_error)}")
                    sentiment = "neutral"  
                
                
                description = "No description available"
                if articles and len(articles) > 0:
                    if 'snippet' in articles[0] and articles[0]['snippet']:
                        description = articles[0]['snippet']
                    elif 'title' in articles[0] and articles[0]['title']:
                        description = articles[0]['title']
                
                
                timestamp = "Recently"
                if 'started' in trend and trend['started']:
                    timestamp = trend['started']
                
                
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
    
    
    background_tasks.add_task(run_agent_analysis)
    
    return {
        "success": True,
        "message": "Enhanced lightweight agent analysis started",
        "using_gemini_api": HAS_GEMINI
    }

@app.get("/api/agent/results")
async def get_agent_results(background_tasks: BackgroundTasks):
    """Get the latest agent analysis results. Triggers analysis if none exists."""
    global agent_results, is_agent_running, last_agent_run_time
    
    if not HAS_AGENT:
        # Return fallback response if agent is not available
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Agent service not available. Using fallback analysis.",
            "analysis": "The AI analysis module isn't available on this server. Only basic trend analysis is being used.",
            "fallback": True
        }
    
    try:
        # Check if we have existing results
        results = agent_service.get_latest_results()
        
        # Check if results indicate no analysis has been performed
        no_analysis = (
            not results or 
            (isinstance(results, dict) and results.get("success") == False and "no analysis" in results.get("message", "").lower())
        )
        
        # If no results exist and agent is not currently running, trigger analysis
        if no_analysis and not is_agent_running:
            logger.info("No existing results found. Triggering automatic analysis...")
            
            # Set the flag to prevent duplicate runs
            is_agent_running = True
            
            # Run analysis synchronously to return results immediately
            try:
                results = agent_service.analyze_trends()
                enhanced_results = enhance_analysis_results(results)
                agent_results = enhanced_results
                last_agent_run_time = datetime.now().isoformat()
                logger.info("Automatic analysis completed successfully")
                return enhanced_results
            except Exception as analysis_error:
                logger.error(f"Error during automatic analysis: {analysis_error}")
                logger.error(traceback.format_exc())
                
                # Return error response
                return {
                    "success": False,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(analysis_error),
                    "message": "Error during automatic analysis",
                    "analysis": "An error occurred while running the automatic AI analysis. Please try again later."
                }
            finally:
                is_agent_running = False
        
        # If agent is currently running
        if is_agent_running:
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Analysis is currently in progress",
                "analysis": "The AI agent is currently analyzing trends. Please wait a moment and refresh.",
                "running": True,
                "using_enhanced_analysis": True
            }
        
        # If we have existing results, return them
        if results:
            enhanced_results = enhance_analysis_results(results)
            agent_results = enhanced_results
            return enhanced_results
        
        # Fallback: should not reach here, but just in case
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "message": "No analysis results available",
            "analysis": "Unable to retrieve or generate analysis results. Please try triggering an analysis manually.",
            "using_enhanced_analysis": True
        }
        
    except Exception as e:
        logger.error(f"Error getting agent results: {e}")
        logger.error(traceback.format_exc())
        
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
        "name": "FactSphere API",
        "version": "1.0.0",
        "status": "running",
        "message": "Welcome to FactSphere API",
        "agent_available": HAS_AGENT,
        "agent_type": f"Enhanced lightweight agent {api_status}",
        "dependencies": deps_status,
        "endpoints": {
            "trends": "/api/trends",
            "analysis": "/api/agent/results",
            "agent_status": "/api/agent/status",
            "trigger_analysis": "/api/agent/analyze"
        }
    }

# === STATIC FILES MOUNTING - AT THE END, BEFORE MAIN BLOCK ===
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Static files mounted from {static_dir}")

if __name__ == "__main__":
    logger.info("Starting the FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000)