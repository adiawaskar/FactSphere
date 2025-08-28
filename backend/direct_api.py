from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
import logging
import traceback
import sys
import os

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
        topic_lower = topic.lower()
        positive_count += sum(1 for word in positive_words if word in topic_lower)
        negative_count += sum(1 for word in negative_words if word in topic_lower)
    
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

@app.get("/")
async def root():
    return {"message": "Welcome to FactSphere API"}

if __name__ == "__main__":
    logger.info("Starting the FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
