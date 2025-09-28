# -------------------- news_fetcher.py --------------------
#agents/fake-news-detection/news_fetcher.py
import requests
import os
from dotenv import load_dotenv
from newspaper import Article  # newspaper3k

load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
BASE_URL = "https://gnews.io/api/v4/search"


def _safe(val, default=""):
    return val if isinstance(val, str) else default


def _fetch_full_text(url, timeout=10):
    """
    Try to download and parse full article text using newspaper3k.
    If it fails, return empty string.
    """
    try:
        art = Article(url)
        art.download()
        art.parse()
        text = art.text or ""
        return text.strip()
    except Exception:
        # silent fail - return empty string, caller can use headline/description fallback
        return ""


def fetch_news_for_claim(keywords, title=None, max_results=20):
    """
    Fetch related news articles using GNews and enrich them with full text via newspaper3k.
    Returns list of dicts:
      {"title": ..., "content": ..., "url": ..., "source": ...}
    """
    if not GNEWS_API_KEY:
        print("[WARN] GNEWS_API_KEY missing. Set it in .env")
        return []

    terms = []
    if title:
        terms.append(f"\"{title}\"")
    if keywords:
        terms.extend(k for k in keywords if k)

    query = " OR ".join(t for t in terms if t)
    if not query:
        return []

    params = {
        "q": query,
        "lang": "en",
        "max": max_results,
        "token": GNEWS_API_KEY
    }

    print(f"[INFO] Fetching news for query: {query}")
    try:
        resp = requests.get(BASE_URL, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", []) or []

        results = []
        seen = set()
        for a in articles:
            url = _safe(a.get("url", ""))
            if not url or url in seen:
                continue
            seen.add(url)

            title_text = _safe(a.get("title", ""))
            descr = _safe(a.get("description", ""))
            # Attempt to fetch full text; fallback to concatenated fields
            full = _fetch_full_text(url)
            combined = " ".join([title_text, descr, full]).strip()
            if not combined:
                continue

            results.append({
                "title": title_text,
                "content": combined,
                "url": url,
                "source": _safe((a.get("source") or {}).get("name", ""))
            })
        print(f"[INFO] Found {len(results)} enriched articles.")
        return results

    except requests.exceptions.HTTPError as e:
        print(f"[WARN] HTTP error fetching news: {e}")
        return []
    except Exception as e:
        print(f"[WARN] Error fetching news: {e}")
        return []
