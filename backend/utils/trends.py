# backend/agents/utils/trends.py
import requests
import json
import os
from datetime import datetime
from collections import Counter
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()


def get_trending_topics(num_trends=5):
    """
    Get trending topics and associated news articles using News API
    Returns a list of trend data dictionaries
    """
    # Get API key from environment variable
    api_key = os.getenv("NEWS_API_KEY", None)
    if not api_key:
        print("Warning: NEWS_API_KEY not found in environment variables")
        print("Get a free API key from https://newsapi.org/")
        return []
    
    trend_data = []
    
    try:
        print("Fetching trending topics...")
        
        # News API endpoint for top headlines
        base_url = "https://newsapi.org/v2/top-headlines"
        
        params = {
            'apiKey': api_key,
            'language': 'en',
            'pageSize': 100,  # Get more articles to analyze trends
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return []
        
        if not data.get('articles'):
            print("No articles found")
            return []
        
        articles = data['articles']
        print(f"Got {len(articles)} articles")
        
        # Use headlines as topics
        topics_created = 0
        processed_articles = set()  # Using a set to track processed article URLs
        
        for article in articles:
            if topics_created >= num_trends:
                break
            
            # Skip if we've already processed this article
            article_url = article.get('url', '')
            if article_url in processed_articles or not article_url:
                continue
                
            headline = article.get('title', 'No title')
            
            # Skip very short headlines or generic headlines
            if len(headline.split()) < 3 or headline.lower() in ["breaking news", "latest updates"]:
                continue
            
            # Create article info for the main article
            main_article_info = {
                'title': headline,
                'source': article.get('source', {}).get('name', 'Unknown'),
                'url': article_url,
                'snippet': article.get('description', '')[:200] if article.get('description') else '',
                'published': article.get('publishedAt', '')
            }
            
            if article.get('urlToImage'):
                main_article_info['image'] = article.get('urlToImage')
            
            # Find related articles with improved similarity matching
            related_articles = [main_article_info]
            processed_articles.add(article_url)
            
            # Extract important keywords from the headline - focus on nouns and proper nouns
            # Remove common words, articles, prepositions
            stop_words = {'a', 'an', 'the', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 
                         'to', 'of', 'and', 'or', 'as', 'is', 'are', 'was', 'were', 'be', 
                         'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                         'but', 'if', 'then', 'else', 'when', 'up', 'down', 'news', 'says', 'say'}
            
            headline_words = headline.lower().split()
            main_keywords = [word.strip('.,!?;:()[]"\'') for word in headline_words 
                            if word.strip('.,!?;:()[]"\'') not in stop_words and len(word) > 2]
            
            # Get the most distinctive words from the headline
            distinctive_words = []
            for word in main_keywords:
                if word[0].isupper() or len(word) > 5:  # Proper nouns or longer words are more distinctive
                    distinctive_words.append(word)
            
            if not distinctive_words and main_keywords:
                distinctive_words = main_keywords[:2]  # Take at least a couple keywords if no distinctive ones
            
            for other_article in articles:
                other_url = other_article.get('url', '')
                if other_url == article_url or other_url in processed_articles or not other_url:
                    continue
                    
                other_title = other_article.get('title', '').lower()
                other_desc = other_article.get('description', '').lower() if other_article.get('description') else ''
                
                # More sophisticated matching - check for distinctive keywords in both title and description
                matches = 0
                for word in distinctive_words:
                    if word.lower() in other_title or word.lower() in other_desc:
                        matches += 1
                
                # Require a higher match threshold - must match multiple distinctive words
                # or have a very strong single match (e.g., a unique proper noun)
                is_related = (matches >= 2) or (matches == 1 and len(distinctive_words) == 1)
                
                if is_related:
                    article_info = {
                        'title': other_article.get('title', 'No title'),
                        'source': other_article.get('source', {}).get('name', 'Unknown'),
                        'url': other_url,
                        'snippet': other_article.get('description', '')[:200] if other_article.get('description') else '',
                        'published': other_article.get('publishedAt', '')
                    }
                    
                    if other_article.get('urlToImage'):
                        article_info['image'] = other_article.get('urlToImage')
                    
                    related_articles.append(article_info)
                    processed_articles.add(other_url)
                    
                    # Get enough related articles but not too many
                    if len(related_articles) >= 3:
                        break
            
            # Only add topics with at least one article (the main one)
            trend_info = {
                'topic': headline,
                'volume': len(related_articles),
                'articles': related_articles
            }
            
            trend_data.append(trend_info)
            topics_created += 1
            print(f"Added topic {topics_created}/{num_trends}: {headline[:50]}... ({len(related_articles)} articles)")
        
        # Save to file
        output_dir = os.path.join(os.path.dirname(__file__), "trend_data")
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"trending_topics_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(trend_data, f, indent=4, ensure_ascii=False)
        
        print(f"Data saved to {filename}")
        print(f"Retrieved {len(trend_data)} topics with a total of {sum(len(t['articles']) for t in trend_data)} news articles")
        
        return trend_data
        
    except requests.exceptions.RequestException as e:
        print(f"API request error: {str(e)}")
        return []
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


# Allow the file to be run as a script for testing
if __name__ == "__main__":
    get_trending_topics()