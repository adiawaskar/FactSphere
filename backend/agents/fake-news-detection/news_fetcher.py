# # # -------------------- news_fetcher.py --------------------
# # import requests
# # import os
# # from dotenv import load_dotenv
# # from newspaper import Article  # newspaper3k
# # import difflib

# # load_dotenv()

# # GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
# # BASE_URL = "https://gnews.io/api/v4/search"


# # def _safe(val, default=""):
# #     return val if isinstance(val, str) else default


# # def _fetch_full_text(url, timeout=10):
# #     """
# #     Try to download and parse full article text using newspaper3k.
# #     If it fails, return empty string.
# #     """
# #     try:
# #         art = Article(url)
# #         art.download()
# #         art.parse()
# #         text = art.text or ""
# #         return text.strip()
# #     except Exception:
# #         # silent fail - return empty string, caller can use headline/description fallback
# #         return ""


# # # def fetch_news_for_claim(keywords, title=None, max_results=20):
# # #     """
# # #     Fetch related news articles using GNews and enrich them with full text via newspaper3k.
# # #     Returns list of dicts:
# # #       {"title": ..., "content": ..., "url": ..., "source": ...}
# # #     """
# # #     if not GNEWS_API_KEY:
# # #         print("[WARN] GNEWS_API_KEY missing. Set it in .env")
# # #         return []

# # #     terms = []
# # #     if title:
# # #         terms.append(f"\"{title}\"")
# # #     if keywords:
# # #         terms.extend(k for k in keywords if k)

# # #     query = " OR ".join(t for t in terms if t)
# # #     if not query:
# # #         return []

# # #     params = {
# # #         "q": query,
# # #         "lang": "en",
# # #         "max": max_results,
# # #         "token": GNEWS_API_KEY
# # #     }

# # #     print(f"[INFO] Fetching news for query: {query}")
# # #     try:
# # #         resp = requests.get(BASE_URL, params=params, timeout=12)
# # #         resp.raise_for_status()
# # #         data = resp.json()
# # #         articles = data.get("articles", []) or []

# # #         results = []
# # #         seen = set()
# # #         for a in articles:
# # #             url = _safe(a.get("url", ""))
# # #             if not url or url in seen:
# # #                 continue
# # #             seen.add(url)

# # #             title_text = _safe(a.get("title", ""))
# # #             descr = _safe(a.get("description", ""))
# # #             # Attempt to fetch full text; fallback to concatenated fields
# # #             full = _fetch_full_text(url)
# # #             combined = " ".join([title_text, descr, full]).strip()
# # #             if not combined:
# # #                 continue

# # #             results.append({
# # #                 "title": title_text,
# # #                 "content": combined,
# # #                 "url": url,
# # #                 "source": _safe((a.get("source") or {}).get("name", ""))
# # #             })
# # #         print(f"[INFO] Found {len(results)} enriched articles.")
# # #         return results

# # #     except requests.exceptions.HTTPError as e:
# # #         print(f"[WARN] HTTP error fetching news: {e}")
# # #         return []
# # #     except Exception as e:
# # #         print(f"[WARN] Error fetching news: {e}")
# # #         return []
# # def _similarity(a, b):
# #     """Compute similarity ratio between two strings."""
# #     return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


# # def fetch_news_for_claim(keywords, title=None, input_url=None, max_results=20, top_k=10):
# #     """
# #     Fetch related news articles using GNews and enrich them with full text via newspaper3k.
# #     Avoids returning the original input URL. Collects across multiple queries.
# #     Returns only the top_k most relevant matches to the title.
# #     """
# #     if not GNEWS_API_KEY:
# #         print("[WARN] GNEWS_API_KEY missing. Set it in .env")
# #         return []

# #     queries = []
# #     if title:
# #         queries.append(f"\"{title}\"")  # exact title
# #     if keywords:
# #         keyword_query = " OR ".join(k for k in keywords if k)
# #         if keyword_query:
# #             queries.append(keyword_query)
# #             if title:
# #                 queries.append(f"\"{title}\" OR {keyword_query}")  # combined

# #     results = []
# #     seen = set()

# #     for q in queries:
# #         params = {
# #             "q": q,
# #             "lang": "en",
# #             "max": max_results,
# #             "token": GNEWS_API_KEY
# #         }
# #         print(f"[INFO] Fetching news for query: {q}")
# #         try:
# #             resp = requests.get(BASE_URL, params=params, timeout=12)
# #             resp.raise_for_status()
# #             data = resp.json()
# #             articles = data.get("articles", []) or []

# #             for a in articles:
# #                 url = _safe(a.get("url", ""))
# #                 if not url or url in seen:
# #                     continue
# #                 if input_url and input_url in url:  # skip original
# #                     continue
# #                 seen.add(url)

# #                 title_text = _safe(a.get("title", ""))
# #                 descr = _safe(a.get("description", ""))
# #                 full = _fetch_full_text(url)
# #                 combined = " ".join([title_text, descr, full]).strip()
# #                 if not combined:
# #                     continue

# #                 # Compute similarity with input title
# #                 sim = _similarity(title or "", title_text)

# #                 results.append({
# #                     "title": title_text,
# #                     "content": combined,
# #                     "url": url,
# #                     "source": _safe((a.get("source") or {}).get("name", "")),
# #                     "similarity": sim
# #                 })

# #         except Exception as e:
# #             print(f"[WARN] Error fetching for {q}: {e}")

# #     # Sort by similarity and return top_k
# #     results = sorted(results, key=lambda x: x["similarity"], reverse=True)
# #     top_results = results[:top_k]

# #     print(f"[INFO] Returning top {len(top_results)} articles (sorted by relevance).")
# #     return top_results

# # -------------------- news_fetcher.py --------------------
# import requests
# import os
# from dotenv import load_dotenv
# from newspaper import Article  # newspaper3k
# import difflib

# load_dotenv()

# GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
# BASE_URL = "https://gnews.io/api/v4/search"


# def _safe(val, default=""):
#     return val if isinstance(val, str) else default


# def _fetch_full_text(url, timeout=10):
#     """
#     Try to download and parse full article text using newspaper3k.
#     If it fails, return empty string.
#     """
#     try:
#         art = Article(url)
#         art.download()
#         art.parse()
#         text = art.text or ""
#         return text.strip()
#     except Exception:
#         # silent fail - return empty string, caller can use headline/description fallback
#         return ""


# def _similarity(a, b):
#     """Compute similarity ratio between two strings."""
#     return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


# def fetch_news_for_claim(keywords, title=None, input_url=None, max_results=20, top_k=10):
#     """
#     Fetch related news articles using GNews and enrich them with full text via newspaper3k.
#     Avoids returning the original input URL. Collects across multiple queries.
#     Returns only the top_k most relevant matches to the title.
#     """
#     if not GNEWS_API_KEY:
#         print("[WARN] GNEWS_API_KEY missing. Set it in .env")
#         return []

#     queries = []
#     if title:
#         queries.append(f"\"{title}\"")  # exact title
#     # if keywords:
#     #     keyword_query = " OR ".join(k for k in keywords if k)
#     #     if keyword_query:
#     #         queries.append(keyword_query)
#     #         if title:
#     #             queries.append(f"\"{title}\" OR {keyword_query}")  # combined

#     results = []
#     seen = set()

#     for q in queries:
#         params = {
#             "q": q,
#             "lang": "en",
#             "max": max_results,
#             "token": GNEWS_API_KEY
#         }
#         print(f"[INFO] Fetching news for query: {q}")
#         try:
#             resp = requests.get(BASE_URL, params=params, timeout=12)
#             resp.raise_for_status()
#             data = resp.json()
#             articles = data.get("articles", []) or []
            
#             print(f"[DEBUG] GNews returned {len(articles)} articles for query: '{q}'")

#             for i, a in enumerate(articles):
#                 url = _safe(a.get("url", ""))
#                 if not url or url in seen:
#                     continue
#                 if input_url and input_url in url:  # skip original
#                     print(f"[DEBUG] Skipping original article: {url}")
#                     continue
#                 seen.add(url)

#                 title_text = _safe(a.get("title", ""))
#                 descr = _safe(a.get("description", ""))
#                 full = _fetch_full_text(url)
#                 combined = " ".join([title_text, descr, full]).strip()
#                 if not combined:
#                     continue

#                 # Compute similarity with input title
#                 sim = _similarity(title or "", title_text)

#                 results.append({
#                     "title": title_text,
#                     "content": combined,
#                     "url": url,
#                     "source": _safe((a.get("source") or {}).get("name", "")),
#                     "similarity": sim
#                 })
                
#                 # DEBUG: Print each article found
#                 print(f"[DEBUG] Article {len(results)}: {title_text}")
#                 print(f"[DEBUG]   Source: {_safe((a.get('source') or {}).get('name', ''))}")
#                 print(f"[DEBUG]   URL: {url}")
#                 print(f"[DEBUG]   Similarity: {sim:.3f}")
#                 print(f"[DEBUG]   ---")

#         except Exception as e:
#             print(f"[WARN] Error fetching for {q}: {e}")

#     # Sort by similarity and return top_k
#     results = sorted(results, key=lambda x: x["similarity"], reverse=True)
#     top_results = results[:top_k]

#     print(f"\n[INFO] Final results: {len(top_results)} articles (sorted by relevance):")
#     for i, article in enumerate(top_results, 1):
#         print(f"[RESULT {i}] Similarity: {article['similarity']:.3f}")
#         print(f"         Title: {article['title']}")
#         print(f"         Source: {article['source']}")
#         print(f"         URL: {article['url']}")
#         print()

#     return top_results
# -------------------- news_fetcher.py (Modified) --------------------
# -------------------- news_fetcher.py (Modified for Broader Search) --------------------



import requests
import os
from dotenv import load_dotenv
from newspaper import Article # newspaper3k
import difflib

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


def _similarity(a, b):
    """Compute similarity ratio between two strings."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def fetch_news_for_claim(keywords, title=None, input_url=None, max_results=50, top_k=10):
    """
    Fetch related news articles using GNews and enrich them with full text via newspaper3k.
    Avoids returning the original input URL. Collects across multiple queries.
    Returns only the top_k most relevant matches to the title.
    
    NOTE: max_results is increased to 50 for a broader search.
    """
    if not GNEWS_API_KEY:
        print("[WARN] GNEWS_API_KEY missing. Set it in .env")
        return []

    queries = []
    
    # --- Generate Multiple, Varied Queries for Broader Search ---
    
    # 1. Exact title search (highest relevance, likely catches original article)
    if title:
        queries.append(f"\"{title}\"")

    # 2. Simplified topic search (keywords joined by space/AND)
    if keywords:
        # Filter out common, short words to focus on core concepts
        core_keywords = [k for k in keywords if len(k) > 3 ]
        if core_keywords:
            keyword_query = " ".join(core_keywords)
            queries.append(keyword_query) # Example: curfew ladakh statehood protests violent

    # 3. High-relevance term search (combining the most unique terms)
    # This query directly targets the *event* details seen in related articles.
    # queries.append("curfew Ladakh protests statehood violent")
    # queries.append("Leh curfew detained")
    
    # Ensure no duplicate queries
    queries = list(dict.fromkeys(queries))
    
    # If the initial title-based query is the only one, add the full title as a regular query too
    if len(queries) == 1 and title:
        queries.append(title)


    results = []
    seen = set()

    for q in queries:
        params = {
            "q": q,
            "lang": "en",
            "max": max_results, # Increased to 50
            "token": GNEWS_API_KEY
        }
        print(f"[INFO] Fetching news for query: {q}")
        try:
            resp = requests.get(BASE_URL, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", []) or []
            
            print(f"[DEBUG] GNews returned {len(articles)} articles for query: '{q}'")

            for i, a in enumerate(articles):
                url = _safe(a.get("url", ""))
                if not url or url in seen:
                    continue
                # Skip the original article
                if input_url and (input_url == url or input_url in url or url in input_url):
                    print(f"[DEBUG] Skipping original article: {url}")
                    continue
                seen.add(url)

                title_text = _safe(a.get("title", ""))
                descr = _safe(a.get("description", ""))
                full = _fetch_full_text(url)
                # Combine title, description, and full text for comprehensive content
                combined = " ".join([title_text, descr, full]).strip()
                if not combined:
                    continue

                # Compute similarity with input title
                sim = _similarity(title or "", title_text)

                results.append({
                    "title": title_text,
                    "content": combined,
                    "url": url,
                    "source": _safe((a.get("source") or {}).get("name", "")),
                    "similarity": sim
                })
                
                # DEBUG: Print each article found
                print(f"[DEBUG] Article {len(results)}: {title_text}")
                print(f"[DEBUG]     Source: {_safe((a.get('source') or {}).get('name', ''))}")
                print(f"[DEBUG]     URL: {url}")
                print(f"[DEBUG]     Similarity: {sim:.3f}")
                print(f"[DEBUG]     ---")

        except Exception as e:
            print(f"[WARN] Error fetching for {q}: {e}")

    # Sort by similarity to the original title and return top_k
    results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    top_results = results[:top_k]

    print(f"\n[INFO] Final results: {len(top_results)} articles (sorted by relevance):")
    for i, article in enumerate(top_results, 1):
        print(f"[RESULT {i}] Similarity: {article['similarity']:.3f}")
        print(f"          Title: {article['title']}")
        print(f"          Source: {article['source']}")
        print(f"          URL: {article['url']}")
        print()

    return top_results