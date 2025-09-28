#backend/api/trend_routes.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.utils.trends import get_trending_topics
import random
from datetime import datetime

router = APIRouter()

def calculate_risk_level(topic: str, articles: List[Dict]) -> str:
    """
    Calculate misinformation risk level based on topic and articles
    In a real system, you would use NLP or ML models
    """
    # Keywords associated with common misinformation topics
    high_risk_keywords = ['hoax', 'conspiracy', 'fraud', 'fake', 'scam']
    medium_risk_keywords = ['claim', 'alleged', 'report', 'rumor']
    
    # Check topic for risk keywords
    if any(keyword in topic.lower() for keyword in high_risk_keywords):
        return "high"
    
    if any(keyword in topic.lower() for keyword in medium_risk_keywords):
        return "medium"
    
    # Simple random distribution for demo purposes
    return random.choice(["low", "medium", "high"])

def calculate_sentiment(topic: str, articles: List[Dict]) -> str:
    """
    Simple sentiment analysis based on keywords
    """
    positive_words = ['good', 'great', 'positive', 'breakthrough', 'success']
    negative_words = ['bad', 'negative', 'fail', 'problem', 'issue', 'controversy']
    
    positive_count = sum(1 for word in positive_words if word in topic.lower())
    negative_count = sum(1 for word in negative_words if word in topic.lower())
    
    # Check article content if available
    for article in articles:
        if 'title' in article:
            positive_count += sum(1 for word in positive_words if word in article['title'].lower())
            negative_count += sum(1 for word in negative_words if word in article['title'].lower())
        if 'snippet' in article:
            positive_count += sum(1 for word in positive_words if word in article['snippet'].lower())
            negative_count += sum(1 for word in negative_words if word in article['snippet'].lower())
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

@router.get("/api/trends")
async def get_trends():
    try:
        # Get trending topics using the function from trends.py
        trends_data = get_trending_topics()
        
        # Format the response for the frontend
        formatted_trends = []
        
        for trend in trends_data:
            topic = trend.get('topic', 'Unknown Topic')
            articles = trend.get('articles', [])
            
            # Get volume or estimate mentions
            mentions = trend.get('volume', random.randint(5000, 50000))
            
            # Calculate risk level and sentiment
            risk_level = calculate_risk_level(topic, articles)
            sentiment = calculate_sentiment(topic, articles)
            
            # Generate a description from articles if available
            description = "No description available"
            if articles and 'snippet' in articles[0]:
                description = articles[0]['snippet']
            elif articles and 'title' in articles[0]:
                description = articles[0]['title']
            
            # Format timestamp
            timestamp = "Recently"
            if 'started' in trend:
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
        
        return {
            "success": True,
            "trends": formatted_trends
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")
