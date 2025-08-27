
import requests
import json
from datetime import datetime


NEWS_API_URL = "https://gnews.io/api/v4/top-headlines?lang=en&max=10&token=API_KEY"


OUTPUT_FILE = "latest_news.json"

def fetch_news():
    url = NEWS_API_URL.replace("API_KEY", "demo")  # 'demo' key gives limited results
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
    print("Fetching latest news...")
    articles = fetch_news()
    if articles:
        save_to_json(articles, OUTPUT_FILE)
    else:
        print("No articles found.")

if __name__ == "__main__":
    main()
