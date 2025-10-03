# news/topic_news_scraper.py
# Topic News Scraper: Fetches news for a specific topic and saves to JSON
import requests
import json
from datetime import datetime


NEWS_API_URL = "https://gnews.io/api/v4/search?lang=en&max=10&q={topic}&token=API_KEY"


OUTPUT_FILE = "topic_news.json"

def fetch_topic_news(topic):
    api_key = "demo" 
    url = NEWS_API_URL.replace("API_KEY", api_key).replace("{topic}", topic)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])
        return articles
    else:
        print(f"Failed to fetch news: {response.status_code}")
        return []

def save_to_json(articles, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(articles)} articles to {filename}")

def main():
    topic = input("Enter a topic to search for news: ")
    print(f"Fetching news for topic: {topic}")
    articles = fetch_topic_news(topic)
    if articles:
        save_to_json(articles, OUTPUT_FILE)
    else:
        print("No articles found.")

if __name__ == "__main__":
    main()
