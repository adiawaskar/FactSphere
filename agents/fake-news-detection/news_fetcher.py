# -------------------- news_fetcher.py --------------------
#agents/fake-news-detection/news_fetcher.py
import requests
import spacy
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import os
from newspaper import Article  # newspaper3k

load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
BASE_URL = "https://gnews.io/api/v4/search"

# Load spaCy model
nlp = spacy.load("en_core_web_sm")


def _safe(text):
    """Safely handle text extraction"""
    return str(text or "").strip()


def _fetch_full_text(url):
    """Fetch full text from URL"""
    try:
        resp = requests.get(url, timeout=10)
        return resp.text[:1000]  # Limit to first 1000 chars
    except:
        return ""


def extract_claim_entities(claim_text):
    """Extract named entities and key topics from claim"""
    doc = nlp(claim_text)
    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],  # Countries, cities, states
        "EVENT": [],
        "DATE": []
    }
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)
    
    return entities


def build_contextual_query(claim_text, title=None):
    """Build more contextual search queries"""
    entities = extract_claim_entities(claim_text)
    
    # Primary query with exact entities
    primary_terms = []
    if title:
        primary_terms.append(f'"{title}"')
    
    # Add important entities with quotes for exact matching
    for person in entities["PERSON"][:2]:
        primary_terms.append(f'"{person}"')
    for org in entities["ORG"][:2]:
        primary_terms.append(f'"{org}"')
    
    # Create multiple targeted queries instead of one broad OR query
    queries = []
    if primary_terms:
        queries.append(" AND ".join(primary_terms[:3]))  # More specific
    if len(primary_terms) > 1:
        queries.append(" OR ".join(primary_terms))  # Fallback
    
    return queries


def fetch_news_for_claim(keywords, title=None, max_results=20, claim_text=""):
    """Enhanced news fetching with multiple targeted queries"""
    if not GNEWS_API_KEY:
        print("[WARN] GNEWS_API_KEY missing. Set it in .env")
        return []

    # Use contextual query building
    full_claim = f"{title} {claim_text}".strip()
    queries = build_contextual_query(full_claim, title)
    
    if not queries:
        # Fallback to original method
        terms = [f'"{title}"'] if title else []
        terms.extend(keywords[:3])  # Limit to top 3 keywords
        queries = [" AND ".join(terms[:2]), " OR ".join(terms)]

    all_articles = []
    seen_urls = set()
    
    for query in queries:
        if len(all_articles) >= max_results:
            break
            
        params = {
            "q": query,
            "lang": "en",
            "max": min(15, max_results - len(all_articles)),
            "token": GNEWS_API_KEY,
            "sortby": "relevance"  # Prioritize relevance over recency
        }

        try:
            resp = requests.get(BASE_URL, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", []) or []
            
            for a in articles:
                url = _safe(a.get("url", ""))
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                # Enhanced relevance filtering
                title_text = _safe(a.get("title", ""))
                if not _is_relevant_to_claim(title_text, full_claim):
                    continue

                descr = _safe(a.get("description", ""))
                full_text = _fetch_full_text(url)
                combined = " ".join([title_text, descr, full_text]).strip()
                
                if len(combined) < 100:  # Skip very short articles
                    continue

                all_articles.append({
                    "title": title_text,
                    "content": combined,
                    "url": url,
                    "source": _safe((a.get("source") or {}).get("name", "")),
                    "relevance_score": _calculate_relevance(combined, full_claim)
                })
                
        except Exception as e:
            print(f"[WARN] Query '{query}' failed: {e}")
            continue

    # Sort by relevance score
    all_articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    print(f"[INFO] Found {len(all_articles)} contextually relevant articles.")
    return all_articles[:max_results]


def _is_relevant_to_claim(article_title, claim_text):
    """Check if article title is actually relevant to the claim"""
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode([article_title.lower(), claim_text.lower()])
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        return similarity > 0.3  # Threshold for relevance
    except:
        # Fallback to keyword overlap
        claim_words = set(claim_text.lower().split())
        title_words = set(article_title.lower().split())
        overlap = len(claim_words.intersection(title_words))
        return overlap >= 2


def _calculate_relevance(article_content, claim_text):
    """Calculate semantic relevance score"""
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Compare claim with article summary
        article_summary = article_content[:500]  # First 500 chars
        embeddings = model.encode([claim_text, article_summary])
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        return similarity
    except:
        return 0.5  # Default relevance
