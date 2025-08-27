import random
from datetime import datetime, timedelta

def fetch_trends():
    """
    Fetch trending misinformation topics.
    In a real application, this would pull data from a database or external API.
    """
    platforms = ['twitter', 'facebook', 'instagram', 'tiktok']
    risk_levels = ['low', 'medium', 'high']
    sentiments = ['positive', 'negative', 'neutral']
    
    topics = [
        {
            "topic": "Climate Change Denial",
            "description": "Claims disputing scientific consensus on climate change",
            "platform": random.choice(platforms),
            "frequency": random.randint(10000, 50000),
            "severity": "high",
            "sentiment": "negative",
            "timestamp": format_time_ago(random.randint(1, 12))
        },
        {
            "topic": "Vaccine Misinformation",
            "description": "False claims about vaccine side effects and efficacy",
            "platform": random.choice(platforms),
            "frequency": random.randint(8000, 40000),
            "severity": "high",
            "sentiment": "negative",
            "timestamp": format_time_ago(random.randint(1, 24))
        },
        {
            "topic": "Election Integrity",
            "description": "Unsubstantiated claims about voting systems",
            "platform": random.choice(platforms),
            "frequency": random.randint(5000, 30000),
            "severity": "medium",
            "sentiment": "neutral",
            "timestamp": format_time_ago(random.randint(2, 48))
        },
        {
            "topic": "AI Conspiracy Theories",
            "description": "Misleading narratives about AI systems and capabilities",
            "platform": random.choice(platforms),
            "frequency": random.randint(3000, 20000),
            "severity": "low",
            "sentiment": "negative",
            "timestamp": format_time_ago(random.randint(4, 72))
        },
        {
            "topic": "Health Supplement Scams",
            "description": "False medical claims about unregulated supplements",
            "platform": random.choice(platforms),
            "frequency": random.randint(2000, 15000),
            "severity": random.choice(risk_levels),
            "sentiment": random.choice(sentiments),
            "timestamp": format_time_ago(random.randint(6, 96))
        }
    ]
    
    return topics

def format_time_ago(hours):
    """Format a timestamp as '2 hours ago', '1 day ago', etc."""
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"
