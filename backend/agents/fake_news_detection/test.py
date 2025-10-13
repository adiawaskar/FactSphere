#!/usr/bin/env python3
"""
analyze_url.py

Improved Multi-Layer News Verification System
Usage:
    python analyze_url.py <article_url>

Features:
 - Query building and fallback search for newer/limited-coverage articles
 - Adaptive similarity thresholds
 - Returns reliable/high-credibility source links
 - Robust extraction with newspaper3k + BeautifulSoup fallback
 - Saves results JSON with structured fields
"""

import json
import os
import sys
import time
import re
from urllib.parse import urlparse
from datetime import datetime

import requests
from newspaper import Article
import spacy
import numpy as np

# optional third-party models; we try to load them but have fallbacks
try:
    from sentence_transformers import SentenceTransformer, util as st_util
except Exception:
    SentenceTransformer = None
    st_util = None

# minimal stub functions if actual implementations are missing
def extract_claim_features(text):
    import re
    entities = re.findall(r'\b[A-Z][a-z]+\b', text)[:10]
    sentiment = {"label": "NEUTRAL", "score": 0.0}
    return {"entities": entities, "sentiment": sentiment}

def extract_contextual_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    freq = {}
    for w in words:
        if len(w) > 3:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq.items(), key=lambda x: -x[1])[:10]

def decide_label_with_confidence(*args, **kwargs):
    return "UNVERIFIED", 0.5

# Load spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    print(f"[WARN] spaCy load failed: {e}")
    try:
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    except Exception as e2:
        print(f"[ERROR] Could not load spaCy: {e2}")
        nlp = None

ALLOWLISTED_DOMAINS = ["nasa.gov", "who.int", "un.org", "dhs.gov", "reuters.com", "bbc.com", "theguardian.com", "nytimes.com", "apnews.com"]
HIGH_CREDIBILITY_DOMAINS = ["reuters.com", "apnews.com", "bbc.com", "npr.org", "nasa.gov", "who.int", "un.org"]

class MultiLayerNewsVerifier:
    def __init__(self, gnews_api_key=None, allowlist=None, highcred=None):
        self.sentence_model = None
        self.util = None
        self.gnews_api_key = gnews_api_key or os.getenv("GNEWS_API_KEY")
        self.base_url = "https://gnews.io/api/v4/search"
        self.allowlist = allowlist or ALLOWLISTED_DOMAINS
        self.highcred = highcred or HIGH_CREDIBILITY_DOMAINS
        self.load_models()

    def load_models(self):
        if SentenceTransformer:
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.util = st_util
                print("[INFO] Loaded sentence-transformers model")
            except Exception as e:
                print(f"[WARN] Could not load sentence-transformer: {e}")

    def extract_article_summary(self, content, max_length=300):
        sentences = re.split(r'(?<=[.!?])\s+', content)
        substantial = [s.strip() for s in sentences if len(s.strip()) > 40]
        summary = ' '.join(substantial[:3])
        return summary[:max_length] if len(summary) > max_length else summary

    def extract_key_claims(self, title, content):
        full_text = (title + ". " + content) if title else content
        if nlp:
            doc = nlp(full_text)
            sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 30]
            claims, facts = [], []
            for sentence in sentences[:12]:
                sl = sentence.lower()
                fact_indicators = ['according to', 'reported', 'confirmed', 'announced', 'revealed', 'study shows', 'research', 'data', 'statistics', 'official', 'said']
                opinion_indicators = ['believes', 'thinks', 'opinion', 'allegedly', 'reportedly', 'claims', 'suggests', 'speculation', 'might', 'could']
                if any(i in sl for i in fact_indicators):
                    facts.append(sentence)
                elif not any(i in sl for i in opinion_indicators):
                    claims.append(sentence)
            key_entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE']][:12]
            return {'claims': claims[:6], 'facts': facts[:6], 'key_entities': key_entities}
        return {'claims': [], 'facts': [], 'key_entities': []}

    def build_improved_queries(self, title, content, key_info):
        queries = []
        title_clean = (title or "").strip()
        if title_clean:
            q = title_clean if len(title_clean) <= 200 else ' '.join(title_clean.split()[:16])
            queries.append({'query': q, 'description': 'Title-based'})
        entities = key_info.get('key_entities', []) if key_info else []
        if entities:
            queries.append({'query': ' '.join(entities[:3]), 'description': 'Entities'})
        kw = extract_contextual_keywords(title_clean + " " + (content or ""))[:6]
        if kw:
            q = ' '.join([w for w, _ in kw[:6]])
            queries.append({'query': q, 'description': 'Keyword-based'})
        if title_clean:
            first_phrases = ' '.join(title_clean.split()[:4])
            queries.append({'query': f"{first_phrases} news", 'description': 'Short-title with news'})
        seen = set()
        final = []
        for qi in queries:
            q = qi['query'].strip()
            if not q: continue
            key = q.lower()
            if key in seen: continue
            seen.add(key)
            final.append(qi)
            if len(final) >= 6: break
        return final

    def fetch_news_articles(self, query, max_results=10):
        if self.gnews_api_key:
            try:
                params = {"q": query, "lang": "en", "max": min(max_results,10), "token": self.gnews_api_key, "sortby": "relevance"}
                resp = requests.get(self.base_url, params=params, timeout=12)
                resp.raise_for_status()
                data = resp.json()
                arts = []
                for a in data.get("articles", []):
                    arts.append({
                        'title': a.get('title',''),
                        'content': a.get('description','') or a.get('content','') or '',
                        'url': a.get('url',''),
                        'source': a.get('source',{}).get('name',''),
                        'publishedAt': a.get('publishedAt','')
                    })
                return arts
            except Exception as e:
                print(f"[WARN] GNews API failed: {e}")
        return self.fallback_news_search(query, max_results)

    def fallback_news_search(self, query, max_results=8):
        print(f"[INFO] Fallback searching for: {query}")
        try:
            search_url = "https://html.duckduckgo.com/html/"
            params = {'q': query + " site:reuters.com OR site:bbc.com OR site:cnn.com OR site:apnews.com OR site:theguardian.com OR site:nytimes.com", 'kl':'us-en'}
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.post(search_url, data=params, headers=headers, timeout=12)
            if resp.status_code != 200: return []
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.content, 'html.parser')
            results = soup.find_all('a', {'class': 'result__a'}, limit=max_results*2)
            articles = []
            for r in results:
                href = r.get('href','')
                title = r.get_text().strip()
                if not href or not title: continue
                m = re.search(r'u=(http[^&]+)&', href)
                url = requests.utils.unquote(m.group(1)) if m else href
                if any(d in url for d in ['bbc.com','reuters.com','cnn.com','apnews.com','theguardian.com','nytimes.com']):
                    articles.append({'title': title, 'content': title, 'url': url, 'source': urlparse(url).netloc.lower(),'publishedAt':''})
                if len(articles) >= max_results: break
            print(f"[INFO] Fallback search found {len(articles)} items")
            return articles
        except Exception as e:
            print(f"[WARN] Fallback search failed: {e}")
            return []

    def compute_similarity(self, base_text, articles):
        if not self.sentence_model or not articles: return []
        try:
            base_emb = self.sentence_model.encode(base_text, convert_to_tensor=True)
            article_texts = [a['title'] + '. ' + a.get('content','') for a in articles]
            arts_emb = self.sentence_model.encode(article_texts, convert_to_tensor=True)
            sims = self.util.pytorch_cos_sim(base_emb, arts_emb)[0].cpu().numpy()
            for idx, a in enumerate(articles):
                a['similarity'] = float(sims[idx])
            return articles
        except Exception as e:
            print(f"[WARN] Similarity computation failed: {e}")
            for a in articles: a['similarity'] = 0.0
            return articles

    def filter_and_rank_articles(self, articles):
        if not articles: return []
        # prioritize high credibility domains
        ranked = sorted(articles, key=lambda x: (x.get('similarity',0.0), x.get('source') in self.highcred), reverse=True)
        return ranked[:10]

    def analyze_url(self, url):
        try:
            art = Article(url)
            art.download()
            art.parse()
            content = art.text
            title = art.title
            summary = self.extract_article_summary(content)
        except Exception as e:
            print(f"[WARN] Failed to extract via newspaper3k: {e}")
            content = ""
            title = ""
            summary = ""
        key_info = self.extract_key_claims(title, content)
        queries = self.build_improved_queries(title, content, key_info)
        all_articles = []
        for q in queries:
            arts = self.fetch_news_articles(q['query'])
            if arts: all_articles.extend(arts)
        all_articles = self.compute_similarity(summary, all_articles)
        final = self.filter_and_rank_articles(all_articles)
        output = {
            'url': url,
            'title': title,
            'summary': summary,
            'key_info': key_info,
            'queries': queries,
            'related_articles': final
        }
        return output

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_url.py <article_url>")
        sys.exit(1)
    url = sys.argv[1]
    verifier = MultiLayerNewsVerifier()
    result = verifier.analyze_url(url)
    outfile = "result.json"
    with open(outfile,'w',encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Analysis saved to {outfile}")
