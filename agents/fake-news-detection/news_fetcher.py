import requests
import os
from dotenv import load_dotenv

load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

NEWS_API_URL = "https://gnews.io/api/v4/search?q={query}&lang=en&max=5&token={api_key}"

def fetch_news_for_claim(keywords):
    """
    Fetch related news articles for a given claim using keywords.
    Returns list of dicts: [{"title": ..., "content": ..., "source": ...}, ...]
    """
    query = "+".join(keywords)
    url = NEWS_API_URL.format(query=query, api_key=GNEWS_API_KEY)

    print(f"[INFO] Fetching news for query: '{query}'")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        simplified = [{"title": a["title"], "content": a.get("content", ""), "source": a.get("url", "")} for a in articles]
        print(f"[INFO] Found {len(simplified)} articles.")
        return simplified
    except requests.exceptions.HTTPError as e:
        print(f"[WARN] HTTP error fetching news: {e}")
        return []
    except Exception as e:
        print(f"[WARN] Error fetching news: {e}")
        return []
