from trendspy import Trends
import json
import os
from datetime import datetime


tr = Trends()

try:
    
    print("Fetching trending topics...")
    trends = tr.trending_now_by_rss(geo='IN')  
    
    
    if trends:
        print(f"Got {len(trends)} trending topics")
        sample_trend = trends[0]
        print(f"Sample trend object type: {type(sample_trend)}")
        print(f"Sample trend object attributes: {dir(sample_trend)}")
    else:
        print("No trending topics found")
    
    
    trend_data = []
    
    
    for i, trend in enumerate(trends):
        
        topic_title = None
        for attr in ['query', 'keyword', 'text', 'title', 'term']:
            if hasattr(trend, attr):
                topic_title = getattr(trend, attr)
                break
        
        if topic_title is None:
            
            topic_title = f"Topic {i+1}" if str(trend) == "" else str(trend)
        
        print(f"Processing topic {i+1}/{len(trends)}: {topic_title}")
        
        
        trend_info = {
            'topic': topic_title,
            'articles': []
        }
        
        
        if hasattr(trend, 'volume'):
            trend_info['volume'] = trend.volume
        if hasattr(trend, 'started'):
            trend_info['started'] = trend.started
        if hasattr(trend, 'link'):
            trend_info['link'] = trend.link
        
        
        if hasattr(trend, 'news') and trend.news:
            print(f"  Found {len(trend.news)} news articles for this topic")
            for article in trend.news:
                try:
                    article_info = {}
                    
                    
                    if hasattr(article, 'title'):
                        article_info['title'] = article.title
                    if hasattr(article, 'source'):
                        article_info['source'] = article.source
                    if hasattr(article, 'url'):
                        article_info['url'] = article.url
                    if hasattr(article, 'snippet'):
                        article_info['snippet'] = article.snippet
                    if hasattr(article, 'time_published'):
                        article_info['published'] = article.time_published
                    
                    
                    if article_info:
                        trend_info['articles'].append(article_info)
                except Exception as e:
                    print(f"Error processing article: {str(e)}")
        else:
            print(f"  No news articles found for this topic")
        
        
        
        if len(trend_info['articles']) < 3:
            try:
                print(f"  Attempting to find more articles for '{topic_title}'...")
                
                related = tr.related_queries(topic_title)
                if related and hasattr(related, 'top'):
                    trend_info['related_queries'] = related.top[:5] if len(related.top) > 5 else related.top
                    print(f"  Found {len(trend_info['related_queries'])} related queries")
            except Exception as e:
                print(f"  Error finding related queries: {str(e)}")
        
        
        trend_data.append(trend_info)
    
    
    output_dir = os.path.join(os.path.dirname(__file__), "trend_data")
    os.makedirs(output_dir, exist_ok=True)
    
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"trending_topics_{timestamp}.json")
    
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(trend_data, f, indent=4, ensure_ascii=False)
    
    print(f"Data saved to {filename}")
    print(f"Retrieved {len(trend_data)} topics with a total of {sum(len(t['articles']) for t in trend_data)} news articles")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    import traceback
    traceback.print_exc()