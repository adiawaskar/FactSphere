import json
import os
import sys
from urllib.parse import urlparse
import requests
from newspaper import Article
import spacy
from datetime import datetime, timedelta
import time
import numpy as np
from collections import Counter
import re

from text_utils import extract_claim_features, extract_contextual_keywords
from evidence_evaluator import EvidenceEvaluator, decide_label_with_confidence

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

ALLOWLISTED_DOMAINS = [
    "nasa.gov", "who.int", "un.org", "dhs.gov", "reuters.com", "bbc.com", "bbc.co.uk",
    "theguardian.com", "nytimes.com", "apnews.com", "timesofindia.indiatimes.com",
    "thehindu.com", "washingtonpost.com", "npr.org", "cnn.com", "abcnews.go.com",
    "edition.cnn.com", "www.bbc.com", "www.reuters.com", "www.theguardian.com",
    "nbcnews.com", "cbsnews.com", "abc.net.au", "news.com.au"
]

HIGH_CREDIBILITY_DOMAINS = [
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "npr.org",
    "nasa.gov", "who.int", "un.org", "gov.uk", "gov.au"
]

class MultiLayerNewsVerifier:
    def __init__(self):
        self.sentence_model = None
        self.gnews_api_key = None
        self.base_url = "https://gnews.io/api/v4/search"
        self.load_models()
        self.load_api_config()
    
    def load_models(self):
        """Load required models for analysis"""
        try:
            from sentence_transformers import SentenceTransformer, util
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.util = util
            print("[INFO] Loaded sentence transformer model")
        except Exception as e:
            print(f"[WARN] Could not load sentence transformer: {e}")

    def load_api_config(self):
        """Load API configuration"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            self.gnews_api_key = os.getenv("GNEWS_API_KEY")
            if not self.gnews_api_key:
                print("[WARN] GNEWS_API_KEY not found in environment variables")
        except ImportError:
            print("[WARN] python-dotenv not installed, trying direct environment access")
            self.gnews_api_key = os.getenv("GNEWS_API_KEY")

    def extract_article_summary(self, content, max_length=300):
        """Extract key sentences from article for comparison"""
        sentences = content.split('. ')
        substantial_sentences = [s.strip() + '.' for s in sentences if len(s.strip()) > 50]
        
        summary = ' '.join(substantial_sentences[:3])
        return summary[:max_length] if len(summary) > max_length else summary

    def extract_key_claims(self, title, content):
        """Extract main claims and facts from the article"""
        full_text = f"{title}. {content}"
        doc = nlp(full_text)
        
        claims = []
        facts = []
        
        sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 30]
        
        for sentence in sentences[:10]:
            sentence_lower = sentence.lower()
            
            fact_indicators = ['according to', 'reported', 'confirmed', 'announced', 'revealed',
                              'study shows', 'research', 'data', 'statistics', 'official']
            
            opinion_indicators = ['believes', 'thinks', 'opinion', 'allegedly', 'reportedly',
                                'claims', 'suggests', 'speculation']
            
            if any(indicator in sentence_lower for indicator in fact_indicators):
                facts.append(sentence)
            elif not any(indicator in sentence_lower for indicator in opinion_indicators):
                claims.append(sentence)
        
        return {
            'claims': claims[:5],
            'facts': facts[:5],
            'key_entities': [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE']][:10]
        }

    def find_similar_articles(self, original_article, max_articles=15):
        """Find articles covering the same story/event with improved search"""
        title = original_article.get('title', '')
        content = original_article.get('content', '')
        url = original_article.get('url', '')
        
        # Extract key information for search
        key_info = self.extract_key_claims(title, content)
        
        # Create improved search queries
        search_queries = self.build_improved_queries(title, content, key_info)
        
        print(f"[INFO] Searching for similar articles with {len(search_queries)} queries")
        
        similar_articles = []
        seen_urls = {url}  # Exclude original article
        
        for query_info in search_queries:
            try:
                print(f"[DEBUG] Trying query: {query_info['query'][:100]}...")
                
                articles = self.fetch_news_articles(query_info['query'], max_results=8)
                
                for article in articles:
                    article_url = article.get('url', '')
                    if article_url in seen_urls:
                        continue
                    
                    seen_urls.add(article_url)
                    
                    # Calculate semantic similarity
                    similarity_score = self.calculate_content_similarity(
                        original_article, article
                    )
                    
                    print(f"[DEBUG] Similarity: {similarity_score:.3f} for {article.get('title', '')[:50]}...")
                    
                    if similarity_score > 0.3:  # Lower threshold for better results
                        article['similarity_score'] = similarity_score
                        article['search_query'] = query_info['description']
                        similar_articles.append(article)
                
            except Exception as e:
                print(f"[WARN] Search query failed: {e}")
                continue
        
        # Sort by similarity and return top articles
        similar_articles.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        print(f"[INFO] Found {len(similar_articles)} similar articles")
        return similar_articles[:max_articles]

    def build_improved_queries(self, title, content, key_info):
        """Build better search queries without complex boolean operators"""
        queries = []
        
        # Query 1: Main entities (simplified)
        main_entities = key_info['key_entities'][:2]  # Only top 2 entities
        if main_entities:
            # Simple entity query without quotes
            entity_query = ' '.join(main_entities)
            queries.append({
                'query': entity_query,
                'description': f'Main entities: {", ".join(main_entities)}'
            })
        
        # Query 2: Key words from title
        title_words = [word for word in title.split() if len(word) > 3 and word.lower() not in ['the', 'and', 'for', 'with', 'from']][:4]
        if title_words:
            queries.append({
                'query': ' '.join(title_words),
                'description': f'Title keywords: {", ".join(title_words)}'
            })
        
        # Query 3: Topic-based query (extract main topic)
        doc = nlp(title)
        topic_words = []
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                not token.is_stop and 
                len(token.text) > 2):
                topic_words.append(token.text)
        
        if topic_words:
            queries.append({
                'query': ' '.join(topic_words[:3]),
                'description': f'Topic words: {", ".join(topic_words[:3])}'
            })
        
        # Query 4: Location-based query if geographical entities found
        locations = [ent.text for ent in nlp(title).ents if ent.label_ == 'GPE']
        if locations:
            queries.append({
                'query': f"{locations[0]} news",
                'description': f'Location-based: {locations[0]}'
            })
        
        return queries[:3]  # Limit to 3 queries to avoid rate limits

    def fetch_news_articles(self, query, max_results=10):
        """Fetch news articles using GNews API with better error handling"""
        if not self.gnews_api_key:
            print("[WARN] No GNEWS API key available, using fallback search")
            return self.fallback_news_search(query, max_results)
        
        params = {
            "q": query,
            "lang": "en",
            "max": min(max_results, 10),  # API limit
            "token": self.gnews_api_key,
            "sortby": "relevance"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            
            # Debug the actual URL being called
            print(f"[DEBUG] API URL: {response.url}")
            
            if response.status_code == 400:
                print(f"[DEBUG] Bad request response: {response.text}")
                # Try with a simpler query
                simple_query = query.split()[0] if query else "news"
                params["q"] = simple_query
                response = requests.get(self.base_url, params=params, timeout=15)
            
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])
            processed_articles = []
            
            for article in articles:
                processed_article = {
                    'title': article.get('title', ''),
                    'content': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'publishedAt': article.get('publishedAt', '')
                }
                processed_articles.append(processed_article)
            
            print(f"[INFO] Fetched {len(processed_articles)} articles via API")
            return processed_articles
            
        except requests.RequestException as e:
            print(f"[WARN] API request failed: {e}")
            return self.fallback_news_search(query, max_results)
        except Exception as e:
            print(f"[WARN] Unexpected API error: {e}")
            return self.fallback_news_search(query, max_results)

    def fallback_news_search(self, query, max_results=5):
        """Fallback search using web scraping when API fails"""
        print(f"[INFO] Using fallback search for: {query}")
        
        try:
            # Use DuckDuckGo search as fallback
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': f"{query} site:bbc.com OR site:reuters.com OR site:cnn.com OR site:theguardian.com",
                'b': '',
                'kl': 'us-en'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                articles = []
                results = soup.find_all('a', {'class': 'result__a'})[:max_results]
                
                for result in results:
                    url = result.get('href', '')
                    title = result.get_text().strip()
                    
                    if url and title and any(domain in url for domain in ['bbc.com', 'reuters.com', 'cnn.com', 'theguardian.com']):
                        articles.append({
                            'title': title,
                            'content': title,  # Use title as content for now
                            'url': url,
                            'source': self._extract_domain(url),
                            'publishedAt': ''
                        })
                
                print(f"[INFO] Fallback search found {len(articles)} articles")
                return articles
                
        except Exception as e:
            print(f"[WARN] Fallback search failed: {e}")
        
        return []

    def calculate_content_similarity(self, original_article, comparison_article):
        """Calculate semantic similarity between articles"""
        if not self.sentence_model:
            return self.calculate_keyword_similarity(original_article, comparison_article)
        
        try:
            # Extract summaries for comparison
            original_text = f"{original_article.get('title', '')} {original_article.get('content', '')}"
            comparison_text = f"{comparison_article.get('title', '')} {comparison_article.get('content', '')}"
            
            original_summary = self.extract_article_summary(original_text)
            comparison_summary = self.extract_article_summary(comparison_text)
            
            # Calculate semantic similarity
            embeddings = self.sentence_model.encode([original_summary, comparison_summary])
            similarity = self.util.cos_sim(embeddings[0], embeddings[1]).item()
            
            # Boost similarity if same entities are mentioned
            entity_boost = self.calculate_entity_overlap(original_article, comparison_article)
            
            final_similarity = min(0.95, similarity + entity_boost)
            return final_similarity
            
        except Exception as e:
            print(f"[WARN] Semantic similarity calculation failed: {e}")
            return self.calculate_keyword_similarity(original_article, comparison_article)

    def calculate_entity_overlap(self, article1, article2):
        """Calculate overlap in named entities"""
        try:
            text1 = f"{article1.get('title', '')} {article1.get('content', '')}"[:1000]
            text2 = f"{article2.get('title', '')} {article2.get('content', '')}"[:1000]
            
            doc1 = nlp(text1)
            doc2 = nlp(text2)
            
            entities1 = set(ent.text.lower() for ent in doc1.ents 
                           if ent.label_ in ['PERSON', 'ORG', 'GPE'])
            entities2 = set(ent.text.lower() for ent in doc2.ents 
                           if ent.label_ in ['PERSON', 'ORG', 'GPE'])
            
            if not entities1 or not entities2:
                return 0
            
            overlap = len(entities1.intersection(entities2))
            union = len(entities1.union(entities2))
            
            return (overlap / union) * 0.2  # Max boost of 0.2
            
        except Exception:
            return 0

    def calculate_keyword_similarity(self, article1, article2):
        """Fallback keyword-based similarity"""
        try:
            text1 = f"{article1.get('title', '')} {article1.get('content', '')}"
            text2 = f"{article2.get('title', '')} {article2.get('content', '')}"
            
            words1 = set(re.findall(r'\b\w+\b', text1.lower()))
            words2 = set(re.findall(r'\b\w+\b', text2.lower()))
            
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words1 = words1 - stop_words
            words2 = words2 - stop_words
            
            if not words1 or not words2:
                return 0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0
            
        except Exception:
            return 0

    def analyze_cross_source_consensus(self, original_article, similar_articles):
        """Analyze consensus across multiple sources"""
        print(f"\n[CONSENSUS] Analyzing consensus across {len(similar_articles)} sources")
        
        if not similar_articles:
            return {
                'consensus_score': 0.1,
                'source_diversity': 0,
                'credible_sources_count': 0,
                'total_sources': 0,
                'unique_sources': 0,
                'contradictions': [],
                'confirmations': [],
                'analysis': 'INSUFFICIENT_SOURCES'
            }
        
        # Analyze source diversity
        sources = [self._extract_domain(article.get('url', '')) for article in similar_articles]
        unique_sources = len(set(sources))
        source_diversity = min(1.0, unique_sources / 5)  # Normalize to max 5 sources
        
        # Count credible sources
        credible_sources = sum(1 for url in [article.get('url', '') for article in similar_articles]
                              if self._is_credible_source(url))
        
        # Analyze content consensus
        original_claims = self.extract_key_claims(
            original_article.get('title', ''),
            original_article.get('content', '')
        )
        
        confirmations = []
        contradictions = []
        
        for article in similar_articles[:8]:  # Analyze top 8 most similar
            article_claims = self.extract_key_claims(
                article.get('title', ''),
                article.get('content', '')
            )
            
            # Check for confirmations and contradictions
            confirmation_score, contradiction_score = self.compare_claims(
                original_claims, article_claims
            )
            
            if confirmation_score > 0.6:
                confirmations.append({
                    'source': self._extract_domain(article.get('url', '')),
                    'similarity': article.get('similarity_score', 0),
                    'confirmation_strength': confirmation_score,
                    'title': article.get('title', '')[:100]
                })
            elif contradiction_score > 0.6:
                contradictions.append({
                    'source': self._extract_domain(article.get('url', '')),
                    'similarity': article.get('similarity_score', 0),
                    'contradiction_strength': contradiction_score,
                    'title': article.get('title', '')[:100]
                })
        
        # Calculate consensus score
        consensus_factors = [
            source_diversity * 0.25,
            min(1.0, credible_sources / 3) * 0.3,  # At least 3 credible sources is good
            min(1.0, len(confirmations) / 3) * 0.35,  # Multiple confirmations
            max(0, 1.0 - len(contradictions) * 0.1) * 0.1  # Penalty for contradictions
        ]
        
        consensus_score = sum(consensus_factors)
        
        # Determine analysis result
        if consensus_score >= 0.75 and credible_sources >= 2:
            analysis = 'STRONG_CONSENSUS'
        elif consensus_score >= 0.6:
            analysis = 'MODERATE_CONSENSUS'
        elif consensus_score >= 0.4:
            analysis = 'WEAK_CONSENSUS'
        elif len(contradictions) > len(confirmations):
            analysis = 'CONTRADICTED'
        else:
            analysis = 'INSUFFICIENT_CONSENSUS'
        
        print(f"[CONSENSUS] Result: {analysis} (score: {consensus_score:.3f})")
        print(f"[CONSENSUS] Confirmations: {len(confirmations)}, Contradictions: {len(contradictions)}")
        
        return {
            'consensus_score': round(consensus_score, 4),
            'source_diversity': round(source_diversity, 3),
            'credible_sources_count': credible_sources,
            'total_sources': len(similar_articles),
            'unique_sources': unique_sources,
            'confirmations': confirmations[:5],  # Top 5
            'contradictions': contradictions[:3],  # Top 3
            'analysis': analysis
        }

    def compare_claims(self, original_claims, comparison_claims):
        """Compare claims between articles to find confirmations/contradictions"""
        if not self.sentence_model:
            return 0.5, 0.1  # Default scores
        
        try:
            original_texts = original_claims['claims'] + original_claims['facts']
            comparison_texts = comparison_claims['claims'] + comparison_claims['facts']
            
            if not original_texts or not comparison_texts:
                return 0.5, 0.1
            
            confirmations = []
            contradictions = []
            
            for orig_claim in original_texts[:3]:
                for comp_claim in comparison_texts[:3]:
                    # Calculate semantic similarity
                    embeddings = self.sentence_model.encode([orig_claim, comp_claim])
                    similarity = self.util.cos_sim(embeddings[0], embeddings[1]).item()
                    
                    if similarity > 0.7:
                        # High similarity indicates confirmation
                        confirmations.append(similarity)
                    elif similarity > 0.4:
                        # Check for contradictory language
                        if self.detect_contradiction(orig_claim, comp_claim):
                            contradictions.append(1 - similarity)
            
            confirmation_score = np.mean(confirmations) if confirmations else 0
            contradiction_score = np.mean(contradictions) if contradictions else 0
            
            return confirmation_score, contradiction_score
            
        except Exception as e:
            print(f"[WARN] Claim comparison failed: {e}")
            return 0.5, 0.1

    def detect_contradiction(self, claim1, claim2):
        """Detect contradictory statements"""
        contradiction_patterns = [
            (r'\bnot\b', r'\bis\b'), (r'\bno\b', r'\byes\b'), (r'\bfalse\b', r'\btrue\b'),
            (r'\bdenied\b', r'\bconfirmed\b'), (r'\brejected\b', r'\baccepted\b')
        ]
        
        claim1_lower = claim1.lower()
        claim2_lower = claim2.lower()
        
        for neg_pattern, pos_pattern in contradiction_patterns:
            if (re.search(neg_pattern, claim1_lower) and re.search(pos_pattern, claim2_lower)) or \
               (re.search(pos_pattern, claim1_lower) and re.search(neg_pattern, claim2_lower)):
                return True
        
        return False

    def _extract_domain(self, url):
        """Extract domain name from URL"""
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith('www.'):
                return domain
            return domain
        except:
            return "unknown"

    def _is_credible_source(self, url):
        """Check if the source is credible"""
        domain = self._extract_domain(url).lower()
        domain_without_www = domain.replace('www.', '') if domain.startswith('www.') else domain
        
        for trusted in ALLOWLISTED_DOMAINS:
            if trusted.lower() in domain or trusted.lower() in domain_without_www:
                return True
        return False

    def _is_high_credibility_source(self, url):
        """Check if the source is high credibility"""
        domain = self._extract_domain(url).lower()
        domain_without_www = domain.replace('www.', '') if domain.startswith('www.') else domain
        
        for trusted in HIGH_CREDIBILITY_DOMAINS:
            if trusted.lower() in domain or trusted.lower() in domain_without_www:
                return True
        return False

def extract_article_from_url(url):
    """Extract article content from URL with better error handling"""
    print(f"[INFO] Attempting to extract content from: {url}")
    
    # Method 1: Try newspaper3k
    try:
        article = Article(url)
        if hasattr(article, 'config'):
            article.config.request_timeout = 20
            article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        article.download()
        
        if article.html and len(article.html) > 1000:
            article.parse()
            
            if article.title and article.text and len(article.text) > 100:
                print(f"[SUCCESS] Extracted via newspaper3k: {len(article.text)} characters")
                return {
                    "title": article.title.strip(),
                    "content": article.text.strip(),
                    "authors": article.authors or [],
                    "publish_date": str(article.publish_date) if article.publish_date else "",
                    "url": url,
                    "source": urlparse(url).netloc.lower(),
                    "extraction_method": "newspaper3k"
                }
    except Exception as e:
        print(f"[WARN] newspaper3k failed: {e}")
    
    # Method 2: BeautifulSoup fallback
    try:
        print("[INFO] Trying direct HTTP request with enhanced headers...")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
        response = session.get(url, timeout=20)
        response.raise_for_status()
        
        if response.status_code == 200 and len(response.content) > 1000:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    element.decompose()
                
                # Extract title
                title = ""
                title_selectors = [
                    'h1[data-testid="headline"]', 'h1.story-headline', 'h1', 
                    '.headline', '.article-title', 'title'
                ]
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem and title_elem.get_text().strip():
                        title = title_elem.get_text().strip()
                        break
                
                # Extract content
                content = ""
                content_selectors = [
                    '[data-component="text-block"]', '[data-testid="ArticleBody"]',
                    'article', '.article-body', '.story-body', '.post-content', 
                    '.entry-content', '.content', 'main'
                ]
                
                for selector in content_selectors:
                    content_divs = soup.select(selector)
                    if content_divs:
                        content_texts = []
                        for div in content_divs:
                            text = div.get_text().strip()
                            if text and len(text) > 20:
                                content_texts.append(text)
                        content = ' '.join(content_texts)
                        if len(content) > 200:
                            break
                
                # Fallback to paragraphs
                if not content or len(content) < 200:
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs 
                                      if len(p.get_text().strip()) > 20])
                
                if title and content and len(content) > 200:
                    print(f"[SUCCESS] Extracted via BeautifulSoup: {len(content)} characters")
                    return {
                        "title": title[:300],
                        "content": content[:8000],
                        "authors": [],
                        "publish_date": "",
                        "url": url,
                        "source": urlparse(url).netloc.lower(),
                        "extraction_method": "beautifulsoup"
                    }
                    
            except ImportError:
                print("[WARN] BeautifulSoup not available")
                
    except Exception as e:
        print(f"[WARN] Direct request failed: {e}")
    
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_url.py <article_url>")
        print("\n🔍 MULTI-LAYER NEWS VERIFICATION SYSTEM")
        print("This system performs comprehensive credibility analysis by:")
        print("1. Extracting and analyzing article content")
        print("2. Finding similar articles from multiple sources")
        print("3. Cross-referencing facts and claims")
        print("4. Analyzing source credibility and consensus")
        print("\nExample: python analyze_url.py 'https://www.bbc.com/news/articles/c98dqyj5dpjo'")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
    except Exception:
        print("[ERROR] Invalid URL format. Please provide a valid HTTP/HTTPS URL.")
        sys.exit(1)
    
    print("🔍 MULTI-LAYER NEWS VERIFICATION SYSTEM")
    print("="*70)
    print(f"[INFO] Analyzing article from: {url}")
    
    # Initialize verifier
    verifier = MultiLayerNewsVerifier()
    
    # Step 1: Extract original article
    print("\n📰 STEP 1: EXTRACTING ARTICLE CONTENT")
    original_article = extract_article_from_url(url)
    if not original_article:
        print("[ERROR] Failed to extract article content.")
        sys.exit(1)
    
    print(f"✅ Extracted: {original_article['title'][:80]}...")
    
    # Step 2: Find similar articles
    print("\n🔍 STEP 2: FINDING SIMILAR ARTICLES")
    similar_articles = verifier.find_similar_articles(original_article)
    
    if not similar_articles:
        print("⚠️  No similar articles found for cross-verification")
        print("    This could be due to:")
        print("    • Very recent news story")
        print("    • Limited API access")
        print("    • Unique/local story with limited coverage")
    else:
        unique_sources = len(set(verifier._extract_domain(a.get('url', '')) for a in similar_articles))
        print(f"✅ Found {len(similar_articles)} similar articles from {unique_sources} different sources")
    
    # Step 3: Analyze consensus
    print("\n🤝 STEP 3: ANALYZING CROSS-SOURCE CONSENSUS")
    consensus_analysis = verifier.analyze_cross_source_consensus(original_article, similar_articles)
    
    # Step 4: Content analysis
    print("\n📊 STEP 4: CONTENT CREDIBILITY ANALYSIS")
    try:
        full_text = f"{original_article['title']}. {original_article['content']}"
        claim_features = extract_claim_features(full_text[:2000])
        
        # Enhanced credibility scoring
        source_credible = verifier._is_credible_source(url)
        high_credible = verifier._is_high_credibility_source(url)
        
        base_score = 0.3
        if high_credible:
            base_score += 0.4
        elif source_credible:
            base_score += 0.25
        
        # Consensus boost
        consensus_boost = consensus_analysis['consensus_score'] * 0.3
        
        # Content quality factors
        entities_count = len(claim_features.get('entities', []))
        if entities_count >= 3:
            base_score += 0.1
        
        sentiment = claim_features.get('sentiment', {})
        if sentiment.get('label') == 'NEUTRAL':
            base_score += 0.05
        
        final_score = min(0.95, base_score + consensus_boost)
        
        # Determine final verdict
        if final_score >= 0.8 and consensus_analysis['analysis'] in ['STRONG_CONSENSUS', 'MODERATE_CONSENSUS']:
            verdict = "HIGHLY_CREDIBLE"
            confidence = final_score
        elif final_score >= 0.65:
            verdict = "LIKELY_CREDIBLE" 
            confidence = final_score
        elif final_score <= 0.35 or consensus_analysis['analysis'] == 'CONTRADICTED':
            verdict = "QUESTIONABLE"
            confidence = 1 - final_score
        else:
            verdict = "UNVERIFIED"
            confidence = 0.5
        
    except Exception as e:
        print(f"[WARN] Content analysis failed: {e}")
        verdict = "UNVERIFIED"
        confidence = 0.5
        final_score = 0.5
    
    # Prepare comprehensive output
    verification_result = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "article": {
            "title": original_article["title"],
            "source": original_article["source"],
            "extraction_method": original_article.get("extraction_method", "unknown")
        },
        "verification": {
            "verdict": verdict,
            "confidence": round(confidence, 4),
            "credibility_score": round(final_score, 4)
        },
        "consensus_analysis": consensus_analysis,
        "similar_articles": [
            {
                "title": art.get('title', '')[:100],
                "source": verifier._extract_domain(art.get('url', '')),
                "similarity": round(art.get('similarity_score', 0), 3),
                "url": art.get('url', '')
            } for art in similar_articles[:10]
        ],
        "content_analysis": {
            "entities_count": entities_count if 'entities_count' in locals() else 0,
            "sentiment": claim_features.get('sentiment', {}).get('label', 'UNKNOWN') if 'claim_features' in locals() else 'UNKNOWN',
            "source_credibility": {
                "is_trusted": source_credible if 'source_credible' in locals() else False,
                "is_high_credibility": high_credible if 'high_credible' in locals() else False
            }
        }
    }
    
    # Save results
    safe_domain = verifier._extract_domain(url).replace('.', '_').replace('www_', '')
    output_file = f"verification_{safe_domain}_{int(time.time())}.json"
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(verification_result, f, indent=4, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"[WARN] Could not save to file: {e}")
    
    # Display final results
    print("\n" + "="*70)
    print("🎯 FINAL VERIFICATION RESULTS")
    print("="*70)
    print(f"📰 Article: {original_article['title'][:60]}...")
    print(f"🌐 Source: {original_article['source']}")
    print(f"⚖️  Verdict: {verdict}")
    print(f"🎯 Confidence: {confidence:.1%}")
    print(f"📊 Credibility Score: {final_score:.1%}")
    print(f"🤝 Consensus: {consensus_analysis['analysis']}")
    print(f"📈 Sources Analyzed: {len(similar_articles)} similar articles")
    print(f"✅ Confirmations: {len(consensus_analysis.get('confirmations', []))}")
    print(f"❌ Contradictions: {len(consensus_analysis.get('contradictions', []))}")
    print("="*70)
    
    if consensus_analysis.get('confirmations'):
        print("\n✅ TOP CONFIRMATIONS:")
        for conf in consensus_analysis['confirmations'][:3]:
            print(f"  • {conf['source']}: {conf['title'][:60]}...")
    
    if consensus_analysis.get('contradictions'):
        print("\n❌ CONTRADICTIONS FOUND:")
        for contra in consensus_analysis['contradictions'][:2]:
            print(f"  • {contra['source']}: {contra['title'][:60]}...")

if __name__ == "__main__":
    main()















# #!/usr/bin/env python3
# """
# analyze_url.py

# Improved Multi-Layer News Verification System
# Usage:
#     python analyze_url.py <article_url>

# Features / improvements:
#  - Improved query building and fallback search for newer/limited-coverage articles
#  - Adaptive similarity thresholds (relaxes when no matches)
#  - Returns reliable/high-credibility source links in output and printout
#  - Robust extraction with newspaper3k + BeautifulSoup fallback
#  - Saves results JSON with structured fields
# """

# import json
# import os
# import sys
# import time
# import re
# from urllib.parse import urlparse
# from datetime import datetime

# import requests
# from newspaper import Article
# import spacy
# import numpy as np

# # optional third-party models; we try to load them but have fallbacks
# try:
#     from sentence_transformers import SentenceTransformer, util as st_util
# except Exception:
#     SentenceTransformer = None
#     st_util = None

# # Local project imports (you mentioned these earlier)
# # These should exist or be stubbed / implemented accordingly.
# # from text_utils import extract_claim_features, extract_contextual_keywords
# # from evidence_evaluator import EvidenceEvaluator, decide_label_with_confidence

# # For demonstration fallback, create simple stubs if imports missing
# def extract_claim_features(text):
#     # Minimal stub: detect some named entities + dummy sentiment
#     # Replace with your real function if available
#     import re
#     entities = re.findall(r'\b[A-Z][a-z]+\b', text)[:10]
#     sentiment = {"label": "NEUTRAL", "score": 0.0}
#     return {"entities": entities, "sentiment": sentiment}

# def extract_contextual_keywords(text):
#     # simple stub
#     words = re.findall(r'\b\w+\b', text.lower())
#     freq = {}
#     for w in words:
#         if len(w) > 3:
#             freq[w] = freq.get(w, 0) + 1
#     # return top 10 as keywords
#     return sorted(freq.items(), key=lambda x: -x[1])[:10]

# def decide_label_with_confidence(*args, **kwargs):
#     return "UNVERIFIED", 0.5

# # Load spaCy
# try:
#     nlp = spacy.load("en_core_web_sm")
# except Exception as e:
#     print(f"[WARN] spaCy model load failed: {e}. Trying to download... (you may need internet)")
#     try:
#         from spacy.cli import download
#         download("en_core_web_sm")
#         nlp = spacy.load("en_core_web_sm")
#     except Exception as e2:
#         print(f"[ERROR] Could not load spaCy: {e2}")
#         nlp = None

# # Trusted domain lists
# ALLOWLISTED_DOMAINS = [
#     "nasa.gov", "who.int", "un.org", "dhs.gov", "reuters.com", "bbc.com", "bbc.co.uk",
#     "theguardian.com", "nytimes.com", "apnews.com", "timesofindia.indiatimes.com",
#     "thehindu.com", "washingtonpost.com", "npr.org", "cnn.com", "abcnews.go.com",
#     "edition.cnn.com", "www.bbc.com", "www.reuters.com", "www.theguardian.com",
#     "nbcnews.com", "cbsnews.com", "abc.net.au", "news.com.au", "gov.uk", "gov.au"
# ]

# HIGH_CREDIBILITY_DOMAINS = [
#     "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "npr.org",
#     "nasa.gov", "who.int", "un.org", "gov.uk", "gov.au", "theguardian.com"
# ]

# class MultiLayerNewsVerifier:
#     def __init__(self, gnews_api_key=None, allowlist=None, highcred=None):
#         self.sentence_model = None
#         self.util = None
#         self.gnews_api_key = gnews_api_key or os.getenv("GNEWS_API_KEY")
#         self.base_url = "https://gnews.io/api/v4/search"
#         self.allowlist = allowlist or ALLOWLISTED_DOMAINS
#         self.highcred = highcred or HIGH_CREDIBILITY_DOMAINS
#         self.load_models()

#     def load_models(self):
#         """Optional load of SentenceTransformer for semantic similarity"""
#         if SentenceTransformer is None:
#             print("[INFO] sentence-transformers not available, semantic similarity disabled.")
#             return
#         try:
#             self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
#             self.util = st_util
#             print("[INFO] Loaded sentence-transformers model 'all-MiniLM-L6-v2'")
#         except Exception as e:
#             print(f"[WARN] Could not load sentence-transformer: {e}")
#             self.sentence_model = None
#             self.util = None

#     def extract_article_summary(self, content, max_length=300):
#         """Return first substantial sentences joined."""
#         sentences = re.split(r'(?<=[.!?])\s+', content)
#         substantial = [s.strip() for s in sentences if len(s.strip()) > 40]
#         summary = ' '.join(substantial[:3])
#         return summary[:max_length] if len(summary) > max_length else summary

#     def extract_key_claims(self, title, content):
#         """
#         Return claims / facts and key entities using spaCy.
#         Conservative extraction to avoid noise.
#         """
#         full_text = (title + ". " + content) if title else content
#         if nlp:
#             doc = nlp(full_text)
#             sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 30]
#             claims = []
#             facts = []
#             for sentence in sentences[:12]:
#                 sl = sentence.lower()
#                 fact_indicators = ['according to', 'reported', 'confirmed', 'announced', 'revealed',
#                                   'study shows', 'research', 'data', 'statistics', 'official', 'said']
#                 opinion_indicators = ['believes', 'thinks', 'opinion', 'allegedly', 'reportedly',
#                                       'claims', 'suggests', 'speculation', 'might', 'could']
#                 if any(i in sl for i in fact_indicators):
#                     facts.append(sentence)
#                 elif not any(i in sl for i in opinion_indicators):
#                     claims.append(sentence)
#             key_entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE']][:12]
#             return {'claims': claims[:6], 'facts': facts[:6], 'key_entities': key_entities}
#         # fallback
#         return {'claims': [], 'facts': [], 'key_entities': []}

#     def build_improved_queries(self, title, content, key_info):
#         """Make a set of diverse queries to increase chances of matches"""
#         queries = []
#         title_clean = (title or "").strip()
#         # Query: exact title (shortened if long)
#         if title_clean:
#             q = title_clean if len(title_clean) <= 200 else ' '.join(title_clean.split()[:16])
#             queries.append({'query': q, 'description': 'Title-based'})

#         # Query: top entities
#         entities = key_info.get('key_entities', []) if key_info else []
#         if entities:
#             queries.append({'query': ' '.join(entities[:3]), 'description': 'Entities'})

#         # Query: keywords from title and content
#         kw = extract_contextual_keywords(title_clean + " " + (content or ""))[:6]
#         if kw:
#             q = ' '.join([w for w, _ in kw[:6]])
#             queries.append({'query': q, 'description': 'Keyword-based'})

#         # Query: short phrase + "news" to broaden
#         if title_clean:
#             first_phrases = ' '.join(title_clean.split()[:4])
#             queries.append({'query': f"{first_phrases} news", 'description': 'Short-title with news'})

#         # Deduplicate and keep several queries (up to 6)
#         seen = set()
#         final = []
#         for qi in queries:
#             q = qi['query'].strip()
#             if not q:
#                 continue
#             key = q.lower()
#             if key in seen:
#                 continue
#             seen.add(key)
#             final.append(qi)
#             if len(final) >= 6:
#                 break
#         return final

#     def fetch_news_articles(self, query, max_results=10):
#         """Try GNews API first; if absent or fails, fallback to scraping DuckDuckGo"""
#         if self.gnews_api_key:
#             params = {
#                 "q": query,
#                 "lang": "en",
#                 "max": min(max_results, 10),
#                 "token": self.gnews_api_key,
#                 "sortby": "relevance"
#             }
#             try:
#                 resp = requests.get(self.base_url, params=params, timeout=12)
#                 # debug
#                 # print(f"[DEBUG] GNews URL: {resp.url}")
#                 resp.raise_for_status()
#                 data = resp.json()
#                 arts = []
#                 for a in data.get("articles", []):
#                     arts.append({
#                         'title': a.get('title', ''),
#                         'content': a.get('description', '') or a.get('content', '') or '',
#                         'url': a.get('url', ''),
#                         'source': a.get('source', {}).get('name', ''),
#                         'publishedAt': a.get('publishedAt', '')
#                     })
#                 return arts
#             except Exception as e:
#                 print(f"[WARN] GNews API failed or unavailable: {e}")

#         # fallback scraping
#         return self.fallback_news_search(query, max_results)

#     def fallback_news_search(self, query, max_results=8):
#         """Use DuckDuckGo HTML search and parse results for known domains"""
#         print(f"[INFO] Fallback searching for: {query}")
#         try:
#             search_url = "https://html.duckduckgo.com/html/"
#             params = {'q': query + " site:reuters.com OR site:bbc.com OR site:cnn.com OR site:apnews.com OR site:theguardian.com OR site:nytimes.com", 'kl': 'us-en'}
#             headers = {'User-Agent': 'Mozilla/5.0'}
#             resp = requests.post(search_url, data=params, headers=headers, timeout=12)
#             if resp.status_code != 200:
#                 return []
#             from bs4 import BeautifulSoup
#             soup = BeautifulSoup(resp.content, 'html.parser')
#             results = soup.find_all('a', {'class': 'result__a'}, limit=max_results*2)
#             articles = []
#             for r in results:
#                 href = r.get('href', '')
#                 title = r.get_text().strip()
#                 if not href or not title:
#                     continue
#                 # Some DuckDuckGo links are redirect wrappers; try to extract real URL
#                 m = re.search(r'u=(http[^&]+)&', href)
#                 url = None
#                 if m:
#                     url = requests.utils.unquote(m.group(1))
#                 else:
#                     url = href
#                 # Basic domain whitelist check
#                 if any(d in url for d in ['bbc.com', 'reuters.com', 'cnn.com', 'apnews.com', 'theguardian.com', 'nytimes.com']):
#                     articles.append({
#                         'title': title,
#                         'content': title,
#                         'url': url,
#                         'source': urlparse(url).netloc.lower(),
#                         'publishedAt': ''
#                     })
#                 if len(articles) >= max_results:
#                     break
#             print(f"[INFO] Fallback search found {len(articles)} items")
#             return articles
#         except Exception as e:
#             print(f"[WARN] fallback search exception: {e}")
#             return []

#     def calculate_content_similarity(self, original_article, comparison_article):
#         """Semantic similarity if model available, otherwise keyword overlap"""
#         if self.sentence_model:
#             try:
#                 orig_text = self.extract_article_summary(original_article.get('title','') + " " + original_article.get('content',''))
#                 comp_text = self.extract_article_summary(comparison_article.get('title','') + " " + comparison_article.get('content',''))
#                 emb = self.sentence_model.encode([orig_text, comp_text])
#                 sim = float(self.util.cos_sim(emb[0], emb[1]).item())
#                 sim = max(0.0, min(1.0, sim))
#                 # small boost if entity overlap
#                 sim += self.calculate_entity_overlap(original_article, comparison_article)
#                 return min(0.95, sim)
#             except Exception as e:
#                 print(f"[WARN] semantic similarity failed: {e}")
#                 return self.calculate_keyword_similarity(original_article, comparison_article)
#         else:
#             return self.calculate_keyword_similarity(original_article, comparison_article)

#     def calculate_entity_overlap(self, article1, article2):
#         try:
#             txt1 = (article1.get('title','') + ' ' + article1.get('content',''))[:1000]
#             txt2 = (article2.get('title','') + ' ' + article2.get('content',''))[:1000]
#             if not nlp:
#                 return 0.0
#             doc1 = nlp(txt1)
#             doc2 = nlp(txt2)
#             e1 = set(ent.text.lower() for ent in doc1.ents if ent.label_ in ['PERSON','ORG','GPE'])
#             e2 = set(ent.text.lower() for ent in doc2.ents if ent.label_ in ['PERSON','ORG','GPE'])
#             if not e1 or not e2:
#                 return 0.0
#             overlap = len(e1 & e2)
#             union = len(e1 | e2)
#             return (overlap / union) * 0.15  # smaller boost
#         except Exception:
#             return 0.0

#     def calculate_keyword_similarity(self, a1, a2):
#         try:
#             t1 = (a1.get('title','') + ' ' + a1.get('content','')).lower()
#             t2 = (a2.get('title','') + ' ' + a2.get('content','')).lower()
#             w1 = set(re.findall(r'\b\w+\b', t1))
#             w2 = set(re.findall(r'\b\w+\b', t2))
#             stop = {'the','and','for','with','from','that','this','what','when','where','which','will'}
#             w1 = w1 - stop
#             w2 = w2 - stop
#             if not w1 or not w2:
#                 return 0.0
#             inter = len(w1 & w2)
#             union = len(w1 | w2)
#             return inter / union if union > 0 else 0.0
#         except Exception:
#             return 0.0

#     def _extract_domain(self, url):
#         try:
#             return urlparse(url).netloc.lower()
#         except:
#             return "unknown"

#     def _is_credible_source(self, url):
#         domain = self._extract_domain(url)
#         for trusted in self.allowlist:
#             if trusted in domain:
#                 return True
#         return False

#     def _is_high_credibility_source(self, url):
#         domain = self._extract_domain(url)
#         for trusted in self.highcred:
#             if trusted in domain:
#                 return True
#         return False

#     def find_similar_articles(self, original_article, max_articles=20):
#         """Try several queries and adapt threshold if few matches found"""
#         title = original_article.get('title','')
#         content = original_article.get('content','')
#         key_info = self.extract_key_claims(title, content)
#         queries = self.build_improved_queries(title, content, key_info)
#         print(f"[INFO] Built {len(queries)} queries for search")

#         similar = []
#         seen = set([original_article.get('url','')])

#         # initial semantic threshold
#         threshold = 0.30
#         attempts = 0
#         while attempts < 3:
#             for qinfo in queries:
#                 q = qinfo['query']
#                 try:
#                     articles = self.fetch_news_articles(q, max_results=8)
#                     for art in articles:
#                         url = art.get('url','')
#                         if not url or url in seen:
#                             continue
#                         seen.add(url)
#                         sim = self.calculate_content_similarity(original_article, art)
#                         art['similarity_score'] = sim
#                         art['search_query'] = qinfo.get('description','')
#                         # If the similarity meets threshold, keep
#                         if sim >= threshold:
#                             similar.append(art)
#                         else:
#                             # keep near-misses in case we lower threshold later
#                             art['_near_miss'] = True
#                             similar.append(art)
#                 except Exception as e:
#                     print(f"[WARN] query failed '{q}': {e}")
#                     continue

#             # sort by similarity desc
#             similar.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)

#             # if enough high similarity results found, stop relaxing
#             high_sim_count = sum(1 for a in similar if a.get('similarity_score',0) >= threshold)
#             if high_sim_count >= min(3, max_articles//4):
#                 break

#             # relax threshold & broaden fetch if not many results
#             attempts += 1
#             threshold = max(0.12, threshold - 0.12)
#             if attempts == 1:
#                 # try additional simple queries built from title tokens
#                 tokens = [tk for tk in (title or "").split() if len(tk) > 3][:6]
#                 if tokens:
#                     extra = ' '.join(tokens[:3]) + " news"
#                     queries.append({'query': extra, 'description': 'Extra title tokens'})
#             elif attempts == 2:
#                 # increase number of fallback fetched articles in later loop
#                 pass

#         # Keep unique urls and keep top max_articles by similarity (prefer known domains)
#         filtered = []
#         used = set()
#         for art in similar:
#             url = art.get('url','')
#             if not url or url in used:
#                 continue
#             used.add(url)
#             filtered.append(art)
#             if len(filtered) >= max_articles:
#                 break

#         # Final filter: if everything low similarity but domains credible, keep them
#         if not any(a.get('similarity_score',0) > 0.25 for a in filtered):
#             # try to keep credible domain articles even if similarity low
#             cred_keep = [a for a in filtered if self._is_credible_source(a.get('url',''))]
#             if cred_keep:
#                 filtered = cred_keep[:max_articles]

#         print(f"[INFO] Found {len(filtered)} similar articles after filtering")
#         return filtered

#     def analyze_cross_source_consensus(self, original_article, similar_articles):
#         """Analyze confirmations / contradictions and compute consensus score"""
#         print(f"\n[CONSENSUS] Analyzing consensus across {len(similar_articles)} sources")

#         if not similar_articles:
#             return {
#                 'consensus_score': 0.0,
#                 'source_diversity': 0,
#                 'credible_sources_count': 0,
#                 'total_sources': 0,
#                 'unique_sources': 0,
#                 'confirmations': [],
#                 'contradictions': [],
#                 'analysis': 'INSUFFICIENT_SOURCES'
#             }

#         # Source diversity
#         sources = [self._extract_domain(a.get('url','')) for a in similar_articles]
#         unique_sources = len(set(sources))
#         source_diversity = min(1.0, unique_sources / 5.0)

#         # credible counts
#         credible_sources = sum(1 for a in similar_articles if self._is_credible_source(a.get('url','')))
#         high_credible_sources = sum(1 for a in similar_articles if self._is_high_credibility_source(a.get('url','')))

#         # Compare claims
#         original_claims = self.extract_key_claims(original_article.get('title',''), original_article.get('content',''))
#         confirmations = []
#         contradictions = []

#         # We'll compare top N articles
#         top_articles = sorted(similar_articles, key=lambda x: x.get('similarity_score',0), reverse=True)[:10]

#         for art in top_articles:
#             comp_claims = self.extract_key_claims(art.get('title',''), art.get('content',''))
#             conf_score, contra_score = self.compare_claims(original_claims, comp_claims)
#             domain = self._extract_domain(art.get('url',''))
#             entry = {
#                 'source': domain,
#                 'title': art.get('title','')[:200],
#                 'url': art.get('url',''),
#                 'similarity': round(art.get('similarity_score',0), 3),
#                 'confirmation_strength': round(conf_score, 3),
#                 'contradiction_strength': round(contra_score, 3),
#                 'is_credible': self._is_credible_source(art.get('url','')),
#                 'is_high_cred': self._is_high_credibility_source(art.get('url',''))
#             }
#             if conf_score > 0.6:
#                 confirmations.append(entry)
#             elif contra_score > 0.55:
#                 contradictions.append(entry)

#         # Consensus scoring components
#         consensus_factors = [
#             source_diversity * 0.25,
#             min(1.0, credible_sources / 3.0) * 0.30,
#             min(1.0, len(confirmations) / 3.0) * 0.40,
#             max(0, 1.0 - len(contradictions) * 0.15) * 0.05
#         ]
#         consensus_score = sum(consensus_factors)

#         # Interpret analysis label
#         if consensus_score >= 0.75 and credible_sources >= 2:
#             analysis = 'STRONG_CONSENSUS'
#         elif consensus_score >= 0.60:
#             analysis = 'MODERATE_CONSENSUS'
#         elif consensus_score >= 0.40:
#             analysis = 'WEAK_CONSENSUS'
#         elif len(contradictions) > len(confirmations) and len(contradictions) >= 1:
#             analysis = 'CONTRADICTED'
#         else:
#             analysis = 'INSUFFICIENT_CONSENSUS'

#         print(f"[CONSENSUS] Result: {analysis} (score: {consensus_score:.3f})")
#         print(f"[CONSENSUS] Confirmations: {len(confirmations)}, Contradictions: {len(contradictions)}")

#         return {
#             'consensus_score': round(consensus_score,4),
#             'source_diversity': round(source_diversity,3),
#             'credible_sources_count': credible_sources,
#             'high_credible_sources_count': high_credible_sources,
#             'total_sources': len(similar_articles),
#             'unique_sources': unique_sources,
#             'confirmations': confirmations[:6],
#             'contradictions': contradictions[:6],
#             'analysis': analysis
#         }

#     def compare_claims(self, original_claims, comparison_claims):
#         """Compare claim texts semantically. Returns (confirmation_score, contradiction_score)"""
#         if not self.sentence_model:
#             # Simple textual overlap fallback
#             orig_texts = original_claims.get('claims',[]) + original_claims.get('facts',[])
#             comp_texts = comparison_claims.get('claims',[]) + comparison_claims.get('facts',[])
#             if not orig_texts or not comp_texts:
#                 return 0.0, 0.0
#             # measure rough overlap
#             max_conf = 0.0
#             max_contra = 0.0
#             for o in orig_texts[:3]:
#                 for c in comp_texts[:3]:
#                     oset = set(re.findall(r'\b\w+\b', o.lower()))
#                     cset = set(re.findall(r'\b\w+\b', c.lower()))
#                     if not oset or not cset:
#                         continue
#                     j = len(oset & cset) / len(oset | cset)
#                     max_conf = max(max_conf, j)
#             # no contradiction detection in fallback
#             return max_conf, max_contra

#         try:
#             orig_texts = original_claims.get('claims',[]) + original_claims.get('facts',[])
#             comp_texts = comparison_claims.get('claims',[]) + comparison_claims.get('facts',[])
#             if not orig_texts or not comp_texts:
#                 return 0.0, 0.0

#             confirmations = []
#             contradictions = []
#             for o in orig_texts[:4]:
#                 for c in comp_texts[:4]:
#                     emb = self.sentence_model.encode([o, c])
#                     sim = float(self.util.cos_sim(emb[0], emb[1]).item())
#                     if sim > 0.70:
#                         confirmations.append(sim)
#                     elif sim > 0.40:
#                         # check contradiction heuristics (basic)
#                         if self.detect_contradiction(o, c):
#                             contradictions.append(1 - sim)
#             conf_score = float(np.mean(confirmations)) if confirmations else 0.0
#             contra_score = float(np.mean(contradictions)) if contradictions else 0.0
#             return conf_score, contra_score
#         except Exception as e:
#             print(f"[WARN] compare_claims failure: {e}")
#             return 0.0, 0.0

#     def detect_contradiction(self, s1, s2):
#         """
#         Heuristic check for contradiction: looks for negation/affirmation mismatch
#         Can be improved with entailment models.
#         """
#         negations = ['not', "n't", 'no', 'never', 'none', 'without']
#         positives = ['is', 'are', 'was', 'were', 'confirmed', 'true', 'yes', 'happened', 'occurred']
#         s1l = s1.lower()
#         s2l = s2.lower()
#         for neg in negations:
#             for pos in positives:
#                 if (neg in s1l and pos in s2l) or (neg in s2l and pos in s1l):
#                     return True
#         # additional antonym pairs
#         antonyms = [('increase','decrease'), ('rise','fall'), ('gain','loss')]
#         for a,b in antonyms:
#             if (a in s1l and b in s2l) or (b in s1l and a in s2l):
#                 return True
#         return False


# def extract_article_from_url(url):
#     """Try newspaper3k then BeautifulSoup fallback"""
#     print(f"[INFO] Attempting to extract content from: {url}")
#     try:
#         article = Article(url)
#         # tweak timeouts if possible
#         if hasattr(article, 'config'):
#             article.config.request_timeout = 20
#             article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
#         article.download()
#         if article.html and len(article.html) > 500:
#             article.parse()
#             if article.title and article.text and len(article.text) > 80:
#                 print(f"[SUCCESS] Extracted via newspaper3k ({len(article.text)} chars)")
#                 return {
#                     "title": article.title.strip(),
#                     "content": article.text.strip(),
#                     "authors": article.authors or [],
#                     "publish_date": str(article.publish_date) if article.publish_date else "",
#                     "url": url,
#                     "source": urlparse(url).netloc.lower(),
#                     "extraction_method": "newspaper3k"
#                 }
#     except Exception as e:
#         print(f"[WARN] newspaper3k failed: {e}")

#     # fallback: HTTP + BeautifulSoup
#     try:
#         print("[INFO] Trying direct HTTP + BeautifulSoup extraction...")
#         session = requests.Session()
#         session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
#             'Accept-Language': 'en-US,en;q=0.9'
#         })
#         r = session.get(url, timeout=20)
#         r.raise_for_status()
#         if r.status_code == 200 and len(r.content) > 800:
#             from bs4 import BeautifulSoup
#             soup = BeautifulSoup(r.content, 'html.parser')
#             for tag in soup(['script','style','nav','footer','header','aside','noscript']):
#                 tag.decompose()
#             # title heuristics
#             title = ""
#             for sel in ['h1', '.headline', '.article-title', 'title']:
#                 elem = soup.select_one(sel)
#                 if elem and elem.get_text().strip():
#                     title = elem.get_text().strip()
#                     break
#             # content heuristics
#             content = ""
#             content_selectors = ['article', '.article-body', '.story-body', '.post-content', '.entry-content', 'main']
#             for sel in content_selectors:
#                 elems = soup.select(sel)
#                 if elems:
#                     texts = []
#                     for e in elems:
#                         txt = e.get_text(separator=' ').strip()
#                         if txt and len(txt) > 100:
#                             texts.append(txt)
#                     if texts:
#                         content = ' '.join(texts)
#                         break
#             if not content:
#                 paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 30]
#                 content = ' '.join(paragraphs)
#             if title and content and len(content) > 200:
#                 print(f"[SUCCESS] Extracted via BeautifulSoup ({len(content)} chars)")
#                 return {
#                     "title": title[:300],
#                     "content": content[:16000],
#                     "authors": [],
#                     "publish_date": "",
#                     "url": url,
#                     "source": urlparse(url).netloc.lower(),
#                     "extraction_method": "beautifulsoup"
#                 }
#     except Exception as e:
#         print(f"[WARN] Direct request extraction failed: {e}")

#     return None


# def main():
#     if len(sys.argv) != 2:
#         print("Usage: python analyze_url.py <article_url>")
#         print("\n🔍 MULTI-LAYER NEWS VERIFICATION SYSTEM")
#         print("Example: python analyze_url.py 'https://www.bbc.com/news/...'")
#         sys.exit(1)

#     url = sys.argv[1]
#     try:
#         parsed = urlparse(url)
#         if not parsed.scheme or not parsed.netloc:
#             raise ValueError("Invalid URL format")
#     except Exception:
#         print("[ERROR] Invalid URL. Provide a valid HTTP/HTTPS URL.")
#         sys.exit(1)

#     print("🔍 MULTI-LAYER NEWS VERIFICATION SYSTEM")
#     print("="*70)
#     print(f"[INFO] Analyzing article: {url}")

#     verifier = MultiLayerNewsVerifier()

#     # Step 1: extract
#     print("\n📰 STEP 1: EXTRACTING ARTICLE CONTENT")
#     original_article = extract_article_from_url(url)
#     if not original_article:
#         print("[ERROR] Failed to extract article content. Aborting.")
#         sys.exit(1)

#     print(f"✅ Extracted: {original_article['title'][:120]}")

#     # Step 2: find similar articles
#     print("\n🔍 STEP 2: FINDING SIMILAR ARTICLES")
#     similar_articles = verifier.find_similar_articles(original_article, max_articles=20)
#     if not similar_articles:
#         print("⚠️ No similar articles found for cross-verification. This may be a very new/local story.")
#     else:
#         unique_sources = len(set(verifier._extract_domain(a.get('url','')) for a in similar_articles))
#         print(f"✅ Found {len(similar_articles)} similar articles from {unique_sources} sources")

#     # Step 3: analyze consensus
#     print("\n🤝 STEP 3: ANALYZING CROSS-SOURCE CONSENSUS")
#     consensus_analysis = verifier.analyze_cross_source_consensus(original_article, similar_articles)

#     # Step 4: content analysis / final scoring
#     print("\n📊 STEP 4: CONTENT CREDIBILITY ANALYSIS")
#     try:
#         full_text = f"{original_article.get('title','')}. {original_article.get('content','')}"
#         claim_features = extract_claim_features(full_text[:4000])

#         # base score
#         source_credible = verifier._is_credible_source(url)
#         high_credible = verifier._is_high_credibility_source(url)

#         base_score = 0.30
#         if high_credible:
#             base_score += 0.35
#         elif source_credible:
#             base_score += 0.20

#         # content richness boost
#         entities_count = len(claim_features.get('entities', []))
#         if entities_count >= 3:
#             base_score += 0.10

#         # sentiment neutrality small boost
#         sentiment = claim_features.get('sentiment', {})
#         if sentiment.get('label') == 'NEUTRAL':
#             base_score += 0.04

#         # consensus boost
#         consensus_boost = consensus_analysis.get('consensus_score', 0.0) * 0.35

#         final_score = min(0.98, base_score + consensus_boost)

#         # determine verdict and confidence
#         if final_score >= 0.80 and consensus_analysis.get('analysis') in ['STRONG_CONSENSUS', 'MODERATE_CONSENSUS']:
#             verdict = "HIGHLY_CREDIBLE"
#             confidence = final_score
#         elif final_score >= 0.65:
#             verdict = "LIKELY_CREDIBLE"
#             confidence = final_score
#         elif final_score <= 0.35 or consensus_analysis.get('analysis') == 'CONTRADICTED':
#             verdict = "QUESTIONABLE"
#             confidence = 1.0 - final_score
#         else:
#             verdict = "UNVERIFIED"
#             confidence = 0.50

#     except Exception as e:
#         print(f"[WARN] Content analysis failed: {e}")
#         verdict = "UNVERIFIED"
#         confidence = 0.5
#         final_score = 0.5
#         entities_count = 0
#         source_credible = False
#         high_credible = False

#     # Collect credible links lists
#     credible_links = []
#     high_credible_links = []
#     for a in similar_articles:
#         u = a.get('url','')
#         if verifier._is_high_credibility_source(u):
#             high_credible_links.append({'source': verifier._extract_domain(u), 'url': u, 'title': a.get('title','')})
#         elif verifier._is_credible_source(u):
#             credible_links.append({'source': verifier._extract_domain(u), 'url': u, 'title': a.get('title','')})

#     # Prepare final JSON result
#     safe_domain = verifier._extract_domain(url).replace('.', '_').replace('www_', '')
#     timestamp = datetime.now().isoformat()
#     result = {
#         "url": url,
#         "timestamp": timestamp,
#         "article": {
#             "title": original_article.get('title',''),
#             "source": original_article.get('source',''),
#             "extraction_method": original_article.get('extraction_method','unknown'),
#             "publish_date": original_article.get('publish_date','')
#         },
#         "verification": {
#             "verdict": verdict,
#             "confidence": round(confidence,4),
#             "credibility_score": round(final_score,4)
#         },
#         "consensus_analysis": consensus_analysis,
#         "similar_articles": [
#             {
#                 "title": a.get('title','')[:200],
#                 "source": verifier._extract_domain(a.get('url','')),
#                 "similarity": round(a.get('similarity_score',0),3),
#                 "url": a.get('url',''),
#                 "is_credible": verifier._is_credible_source(a.get('url','')),
#                 "is_high_cred": verifier._is_high_credibility_source(a.get('url',''))
#             } for a in similar_articles
#         ],
#         "credible_sources": credible_links,
#         "high_credibility_sources": high_credible_links,
#         "content_analysis": {
#             "entities_count": entities_count,
#             "sentiment": claim_features.get('sentiment', {}).get('label', 'UNKNOWN'),
#             "source_credibility": {
#                 "is_trusted": source_credible,
#                 "is_high_credibility": high_credible
#             }
#         }
#     }

#     # Save JSON
#     outfilename = f"verification_{safe_domain}_{int(time.time())}.json"
#     try:
#         with open(outfilename, 'w', encoding='utf-8') as f:
#             json.dump(result, f, indent=4, ensure_ascii=False)
#         print(f"\n💾 Results saved to: {outfilename}")
#     except Exception as e:
#         print(f"[WARN] Could not save result file: {e}")

#     # Print summary
#     print("\n" + "="*70)
#     print("🎯 FINAL VERIFICATION RESULTS")
#     print("="*70)
#     print(f"📰 Article: {original_article.get('title','')[:120]}")
#     print(f"🌐 Source: {original_article.get('source','')}")
#     print(f"⚖️  Verdict: {verdict}")
#     print(f"🎯 Confidence: {confidence:.1%}")
#     print(f"📊 Credibility Score: {final_score:.1%}")
#     print(f"🤝 Consensus Status: {consensus_analysis.get('analysis')}")
#     print(f"📈 Sources Analyzed: {len(similar_articles)}")
#     print(f"✅ Confirmations: {len(consensus_analysis.get('confirmations',[]))}")
#     print(f"❌ Contradictions: {len(consensus_analysis.get('contradictions',[]))}")
#     print("="*70)

#     if consensus_analysis.get('confirmations'):
#         print("\n✅ TOP CONFIRMATIONS:")
#         for conf in consensus_analysis['confirmations'][:5]:
#             print(f"  • {conf['source']}: {conf['title'][:80]} ({conf['url']})")

#     if consensus_analysis.get('contradictions'):
#         print("\n❌ CONTRADICTIONS FOUND:")
#         for c in consensus_analysis['contradictions'][:5]:
#             print(f"  • {c['source']}: {c['title'][:80]} ({c['url']})")

#     if high_credible_links:
#         print("\n🔷 HIGH-CREDIBILITY SOURCES (links):")
#         for h in high_credible_links:
#             print(f"  • {h['source']}: {h['title'][:80]}  -> {h['url']}")

#     if credible_links:
#         print("\n🔹 CREDIBLE SOURCES (links):")
#         for c in credible_links:
#             print(f"  • {c['source']}: {c['title'][:80]}  -> {c['url']}")

#     print("\n" + "="*70)
#     print("Saved JSON contains full structured results including similar article URLs.")
#     print("="*70)


# if __name__ == "__main__":
#     main()




# import sys
# import json
# import logging
# import requests
# import feedparser
# from newspaper import Article
# from sentence_transformers import SentenceTransformer, util

# # ----------------------------
# # Setup logging with colorful markers
# # ----------------------------
# logging.basicConfig(level=logging.INFO, format='%(message)s')
# logger = logging.getLogger("NewsVerifier")

# # Emoji markers
# INFO = "[INFO]"
# SUCCESS = "✅"
# FAIL = "❌"
# STEP = "🔍"

# # ----------------------------
# # Load NLP model
# # ----------------------------
# model = SentenceTransformer("all-MiniLM-L6-v2")

# # ----------------------------
# # Extract article text
# # ----------------------------
# def extract_text(url):
#     print("\n📰 STEP 1: EXTRACTING ARTICLE CONTENT")
#     try:
#         article = Article(url)
#         article.download()
#         article.parse()
#         print(f"{SUCCESS} Extracted: {article.title}")
#         return article.title, article.text
#     except Exception as e:
#         print(f"{FAIL} Failed to extract article: {e}")
#         return None, None

# # ----------------------------
# # Search similar articles via Google News RSS
# # ----------------------------
# def search_google_news(query, max_results=10):
#     print("\n🔍 STEP 2: FINDING SIMILAR ARTICLES")
#     print(f"{INFO} Searching Google News for: {query}")
#     url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
#     feed = feedparser.parse(url)
#     results = []
#     for entry in feed.entries[:max_results]:
#         results.append({
#             "title": entry.title,
#             "link": entry.link,
#             "published": entry.published if "published" in entry else ""
#         })
#     if results:
#         print(f"{SUCCESS} Found {len(results)} related articles")
#     else:
#         print(f"⚠️ No similar articles found")
#     return results

# # ----------------------------
# # Get consensus score
# # ----------------------------
# def consensus_check(main_text, sources):
#     print("\n🤝 STEP 3: ANALYZING CROSS-SOURCE CONSENSUS")
#     if not sources:
#         print("⚠️ No sources available for consensus check")
#         return 0, []

#     embeddings_main = model.encode(main_text, convert_to_tensor=True)
#     agreements = []
#     total_score = 0

#     for s in sources:
#         try:
#             art = Article(s["link"])
#             art.download()
#             art.parse()
#             if not art.text:
#                 continue
#             emb = model.encode(art.text, convert_to_tensor=True)
#             sim = float(util.cos_sim(embeddings_main, emb))
#             agreements.append({"source": s["link"], "similarity": sim})
#             total_score += sim
#         except Exception:
#             continue

#     if not agreements:
#         print("⚠️ Could not calculate consensus (no valid content)")
#         return 0, []
#     avg_score = total_score / len(agreements)
#     print(f"{SUCCESS} Consensus score calculated: {round(avg_score,3)}")
#     return avg_score, agreements

# # ----------------------------
# # Credibility scoring (simple)
# # ----------------------------
# def credibility_score(consensus):
#     if consensus > 0.75:
#         return "LIKELY_CREDIBLE", 85
#     elif consensus > 0.5:
#         return "POSSIBLY_CREDIBLE", 65
#     else:
#         return "LOW_CONFIDENCE", 40

# # ----------------------------
# # Main pipeline
# # ----------------------------
# def analyze_url(url):
#     print("\n======================================================================")
#     print("🔍 MULTI-LAYER NEWS VERIFICATION SYSTEM")
#     print("======================================================================")

#     title, text = extract_text(url)
#     if not text:
#         return {"error": "Could not extract article."}

#     # Step 1: Search for related articles
#     sources = search_google_news(title)

#     # Step 2: Consensus check
#     consensus, agreements = consensus_check(text, sources)

#     # Step 3: Credibility scoring
#     verdict, score = credibility_score(consensus)

#     print("\n======================================================================")
#     print("🎯 FINAL VERIFICATION RESULTS")
#     print("======================================================================")
#     print(f"📰 Article: {title}")
#     print(f"🌐 Source: {url.split('/')[2]}")
#     print(f"⚖️  Verdict: {verdict}")
#     print(f"📊 Credibility Score: {score}%")
#     print(f"📈 Sources Analyzed: {len(agreements)}")
#     print("======================================================================\n")

#     result = {
#         "article_title": title,
#         "original_url": url,
#         "consensus_score": round(consensus, 3),
#         "credibility": verdict,
#         "credibility_score": score,
#         "supporting_articles": agreements
#     }

#     return result

# # ----------------------------
# # CLI entry
# # ----------------------------
# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python news_verifier.py <url>")
#         sys.exit(1)

#     url = sys.argv[1]
#     output = analyze_url(url)

#     # Save JSON result
#     fname = f"verification_{url.split('//')[1].split('/')[0]}.json"
#     with open(fname, "w", encoding="utf-8") as f:
#         json.dump(output, f, indent=2)
#     print(f"💾 Results saved to: {fname}")
