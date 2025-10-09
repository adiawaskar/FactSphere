#backend/agents/misinformation_agent_lite.py
"""
Lightweight misinformation detection agent.
Uses smaller models and optimizations for systems with limited memory.
Optional integration with Gemini API for enhanced analysis.
"""

import logging
import traceback
import os
import sys
from datetime import datetime
import json
import random
import re
from typing import Dict, List, Any, Optional
import urllib.parse
import hashlib
import difflib
import itertools
from collections import defaultdict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import json
import re
from typing import List, Dict, Any
import dotenv


dotenv.load_dotenv()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("misinformation-agent-lite")

# Try to import requests for API calls
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    logger.warning("Could not import requests library. API integrations will be disabled.")
    HAS_REQUESTS = False

# Set path to include parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import trends utility
logger.info(f"Current working directory: {os.getcwd()}")
from utils.trends import get_trending_topics
HAS_TRENDS_IMPORT = True
logger.info("Successfully imported get_trending_topics")

# Try to import ML libraries
try:
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.ensemble import RandomForestClassifier
    import nltk
    HAS_NLTK = True
    
    # Download minimal NLTK data
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
    except Exception as e:
        logger.warning(f"Could not download NLTK data: {str(e)}")
        
except ImportError:
    logger.warning("Could not import scikit-learn or NLTK. Using rule-based fallback mode.")
    HAS_NLTK = False

# Check for Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
HAS_GEMINI_API = GEMINI_API_KEY is not None
if HAS_GEMINI_API:
    logger.info("Gemini API integration is available")
else:
    logger.info("Gemini API integration is not available - using lightweight analysis only")

# Enhanced misinformation indicators with categories
MISINFORMATION_INDICATORS = {
    "claim_language": [
        "reportedly", "allegedly", "supposedly", "claimed", "rumored", 
        "said to be", "purportedly", "ostensibly"
    ],
    "falsehoods": [
        "hoax", "conspiracy", "fake", "false", "rumor", "debunked", "misleading",
        "unverified", "scam", "fraud", "deceive", "untrue", "fabricated",
        "propaganda", "inaccurate", "not credible", "disproven", "unfounded"
    ],
    "emotional_manipulation": [
        "shocking", "unbelievable", "outrageous", "bombshell", "alarming", 
        "incredible", "mind-blowing", "jaw-dropping", "you won't believe"
    ],
    "urgency": [
        "urgent", "breaking", "alert", "warning", "must know", "attention",
        "act now", "emergency"
    ],
    "overgeneralizations": [
        "always", "never", "everyone", "no one", "all", "none", "proven",
        "definitely", "absolutely", "undeniable", "certainly"
    ]
}

# Flattened version for simple lookups
MISINFORMATION_KEYWORDS = [word for category in MISINFORMATION_INDICATORS.values() for word in category]

# Enhanced credibility indicators with categories
CREDIBILITY_INDICATORS = {
    "expert_sources": [
        "according to experts", "research shows", "studies indicate",
        "scientists found", "evidence suggests", "analysis reveals",
        "researchers discovered", "experts confirm"
    ],
    "verification": [
        "verified by", "confirmed by", "fact check", "evidence-based",
        "peer-reviewed", "scientific consensus", "official statement",
        "independently verified", "multiple sources confirm"
    ],
    "nuanced_language": [
        "may", "might", "could", "suggests", "indicates", "appears to",
        "evidence points to", "is consistent with", "is associated with"
    ],
    "transparency": [
        "correction", "update", "editor's note", "clarification",
        "source provided", "methodology explained", "data available",
        "limitations noted"
    ]
}

# Flattened version for simple lookups
CREDIBILITY_KEYWORDS = [phrase for category in CREDIBILITY_INDICATORS.values() for phrase in category]

# Known credible and problematic domain lists
CREDIBLE_DOMAINS = [
    "reuters.com", "apnews.com", "npr.org", "bbc.com", "bbc.co.uk", 
    "nytimes.com", "washingtonpost.com", "wsj.com", "economist.com", 
    "nature.com", "science.org", "nejm.org", "pnas.org", "who.int", 
    "nih.gov", "cdc.gov", "fda.gov", "europa.eu", "un.org"
]

PROBLEMATIC_DOMAINS = [
    "theonion.com",  # Satire, not actual misinformation but can be misunderstood
    "nationalreport.net", "worldnewsdailyreport.com", "empirenews.net",
    "huzlers.com", "infowars.com", "naturalnews.com", "dailybuzzlive.com",
    "newsbiscuit.com", "clickhole.com"  # More satire
]

class LightweightMisinformationAgent:
    """A lightweight misinformation analysis agent with enhanced analysis capabilities."""
    
    def __init__(self):
        """Initialize the lightweight agent."""
        self.latest_results = None
        self.model = None
        self.vectorizer = None
        
        if HAS_NLTK:
            # Use TF-IDF instead of simple counts for better feature representation
            self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            # RandomForest tends to be more accurate than NB for text classification
            self.model = RandomForestClassifier(n_estimators=50, random_state=42) if HAS_NLTK else MultinomialNB()
            self._train_simple_model()
    
    def _train_simple_model(self):
        """Train a simple model for misinformation detection with an expanded dataset."""
        try:
            # Enhanced training dataset with more examples
            texts = [
                # Credible content examples (class 0)
                "This is a factual statement based on scientific evidence.",
                "Research shows that this approach is effective.",
                "According to experts, this claim is accurate.",
                "Official sources confirm this information.",
                "Studies indicate that this is correct.",
                "This is a verified fact.",
                "The consensus among scientists supports this.",
                "Multiple independent sources have confirmed this information.",
                "Peer-reviewed research published in Nature suggests this conclusion.",
                "The World Health Organization has verified these findings.",
                "A systematic review of 42 studies found consistent evidence supporting this claim.",
                "This conclusion is based on data from three independent laboratories.",
                "According to the CDC, these preventive measures are effective.",
                "Statistical analysis of the data supports this interpretation.",
                "This explanation aligns with the current scientific understanding.",
                
                # Misinformation examples (class 1)
                "This conspiracy theory has been debunked.",
                "This is a hoax spreading on social media.",
                "This is fake news without any evidence.",
                "This rumor has been proven false.",
                "This is misleading and takes facts out of context.",
                "This is a fabricated claim with no basis in reality.",
                "This false information is spreading online.",
                "This scam is targeting vulnerable people.",
                "This claim contradicts established scientific consensus.",
                "SHOCKING: You won't believe what they're hiding from you!",
                "They don't want you to know this one weird trick!",
                "Scientists are BAFFLED by this miraculous cure they're keeping secret!",
                "This BOMBSHELL revelation will change everything you thought you knew!",
                "The mainstream media is covering up this EXPLOSIVE truth!",
                "What doctors DON'T want you to know about this cure!"
            ]
            
            labels = [0] * 15 + [1] * 15  # 0 = credible, 1 = misinformation
            
            # Vectorize and train
            X = self.vectorizer.fit_transform(texts)
            self.model.fit(X, labels)
            logger.info("Enhanced misinformation classifier trained successfully")
            
        except Exception as e:
            logger.error(f"Error training enhanced model: {str(e)}")
            self.model = None
    
    def _assess_domain_credibility(self, url: str) -> Dict[str, Any]:
        """Assess the credibility of a domain."""
        result = {
            "domain": "",
            "is_credible_source": False,
            "is_problematic_source": False,
            "score": 0.5  # Neutral by default
        }
        
        if not url or not isinstance(url, str):
            return result
        
        try:
            # Extract domain from URL
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            
            result["domain"] = domain
            
            # Check against known lists
            if any(domain.endswith(cred_domain) for cred_domain in CREDIBLE_DOMAINS):
                result["is_credible_source"] = True
                result["score"] = 0.2  # More likely to be credible
            
            if any(domain.endswith(prob_domain) for prob_domain in PROBLEMATIC_DOMAINS):
                result["is_problematic_source"] = True
                result["score"] = 0.8  # More likely to contain misinformation
            
            return result
        except Exception as e:
            logger.error(f"Error assessing domain credibility: {str(e)}")
            return result
    
    def analyze_text(self, text: str, sources: List[str] = None) -> Dict[str, Any]:
        """
        Analyze a text for misinformation indicators with enhanced analysis.
        
        Args:
            text: The text to analyze
            sources: Optional list of source URLs to assess
            
        Returns:
            Analysis results including misinformation score, confidence, and justification
        """
        result = {
            "misinformation_score": 0.5,  # Default middle score
            "confidence": 0.0,
            "credibility_indicators": [],
            "credibility_categories": {},
            "misinformation_indicators": [],
            "misinformation_categories": {},
            "domain_analysis": [],
            "justification": "Insufficient information to make a determination."
        }
        
        if not text:
            return result
        
        try:
            # 1. Basic keyword analysis with categorization
            text_lower = text.lower()
            
            # Count and categorize misinformation indicators
            misinfo_categories = {}
            for category, keywords in MISINFORMATION_INDICATORS.items():
                found_keywords = [k for k in keywords if k in text_lower]
                if found_keywords:
                    misinfo_categories[category] = found_keywords
            
            # Count and categorize credibility indicators
            cred_categories = {}
            for category, phrases in CREDIBILITY_INDICATORS.items():
                found_phrases = [p for p in phrases if p in text_lower]
                if found_phrases:
                    cred_categories[category] = found_phrases
            
            # Flatten for backward compatibility
            misinfo_keywords = [k for keywords in misinfo_categories.values() for k in keywords]
            cred_keywords = [p for phrases in cred_categories.values() for p in phrases]
            
            # Store in result
            result["misinformation_indicators"] = misinfo_keywords
            result["credibility_indicators"] = cred_keywords
            result["misinformation_categories"] = misinfo_categories
            result["credibility_categories"] = cred_categories
            
            # 2. Domain credibility analysis
            if sources:
                domain_analyses = [self._assess_domain_credibility(url) for url in sources]
                result["domain_analysis"] = domain_analyses
                
                # Factor domain credibility into the analysis
                credible_domains = sum(1 for d in domain_analyses if d["is_credible_source"])
                problematic_domains = sum(1 for d in domain_analyses if d["is_problematic_source"])
                
                # Adjust scores based on sources
                if credible_domains > 0:
                    cred_keywords.extend(["credible source"] * credible_domains)
                if problematic_domains > 0:
                    misinfo_keywords.extend(["problematic source"] * problematic_domains)
            
            # 3. Calculate basic score with enhanced weighting
            misinfo_count = len(misinfo_keywords)
            cred_count = len(cred_keywords)
            
            if misinfo_count + cred_count > 0:
                # Weighted scoring - urgent and emotional language weigh more heavily
                urgent_emotional_count = len(misinfo_categories.get("urgency", [])) + len(misinfo_categories.get("emotional_manipulation", []))
                
                # Base score
                result["misinformation_score"] = (misinfo_count + urgent_emotional_count * 0.5) / (misinfo_count + cred_count + 1)
                result["confidence"] = min(0.5, (misinfo_count + cred_count) / 15)
            
            # 4. ML model analysis if available
            ml_score = None
            if HAS_NLTK and self.model and self.vectorizer:
                try:
                    X = self.vectorizer.transform([text])
                    if hasattr(self.model, "predict_proba"):
                        proba = self.model.predict_proba(X)[0]
                        ml_score = proba[1]  # Probability of misinformation class
                    else:
                        prediction = self.model.predict(X)[0]
                        ml_score = float(prediction)  # 0 for credible, 1 for misinformation
                    
                    # Blend rule-based and ML scores
                    result["misinformation_score"] = (result["misinformation_score"] + ml_score) / 2
                    result["confidence"] = min(0.8, result["confidence"] + 0.3)
                    
                except Exception as ml_error:
                    logger.warning(f"Error using ML model: {str(ml_error)}")
            
            # 5. Generate a justification
            justifications = []
            
            # Add explanations based on detected patterns
            if misinfo_count > 0:
                if "emotional_manipulation" in misinfo_categories:
                    justifications.append(f"Contains emotional or sensationalist language ({', '.join(misinfo_categories['emotional_manipulation'][:3])}).")
                
                if "urgency" in misinfo_categories:
                    justifications.append(f"Uses urgency to create pressure ({', '.join(misinfo_categories['urgency'][:3])}).")
                
                if "overgeneralizations" in misinfo_categories:
                    justifications.append(f"Contains overgeneralizations ({', '.join(misinfo_categories['overgeneralizations'][:3])}).")
                
                if "falsehoods" in misinfo_categories:
                    justifications.append(f"Contains terms associated with misinformation ({', '.join(misinfo_categories['falsehoods'][:3])}).")
            
            if cred_count > 0:
                if "expert_sources" in cred_categories:
                    justifications.append(f"Cites expert sources ({', '.join(cred_categories['expert_sources'][:3])}).")
                
                if "verification" in cred_categories:
                    justifications.append(f"Mentions verification processes ({', '.join(cred_categories['verification'][:3])}).")
                
                if "nuanced_language" in cred_categories:
                    justifications.append(f"Uses nuanced language that acknowledges uncertainty ({', '.join(cred_categories['nuanced_language'][:3])}).")
            
            # Add domain-based justifications
            if sources:
                if credible_domains > 0:
                    justifications.append(f"Cites {credible_domains} generally credible source(s).")
                if problematic_domains > 0:
                    justifications.append(f"Cites {problematic_domains} potentially problematic source(s).")
            
            # Add ML-based explanation if available
            if ml_score is not None:
                ml_judgment = "likely misinformation" if ml_score > 0.6 else "potentially credible" if ml_score < 0.4 else "uncertain"
                justifications.append(f"Automated content analysis suggests this is {ml_judgment}.")
            
            # Generate the final justification text
            if justifications:
                risk_level = "high" if result["misinformation_score"] > 0.7 else "medium" if result["misinformation_score"] > 0.4 else "low"
                result["justification"] = f"This content has a {risk_level} risk of containing misinformation. " + " ".join(justifications)
            
            # 6. Optional Gemini API integration for deeper analysis
            if HAS_GEMINI_API and text and len(text) > 50:
                try:
                    gemini_result = self._analyze_with_gemini(text)
                    if gemini_result and "analysis" in gemini_result:
                        # Include Gemini's analysis but keep our basic score as primary
                        result["gemini_analysis"] = gemini_result["analysis"]
                        if "score" in gemini_result:
                            # Blend with our score but with lower weight (30%)
                            gemini_score = gemini_result["score"]
                            result["misinformation_score"] = result["misinformation_score"] * 0.7 + gemini_score * 0.3
                        result["justification"] += f"\n\nAI analysis: {gemini_result.get('justification', '')}"
                except Exception as api_error:
                    logger.warning(f"Error using Gemini API: {str(api_error)}")
            
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
        
        return result
    
    

    def _analyze_with_gemini(self, text: str, sources: List[str] = None, contradiction_data: Dict = None) -> Dict[str, Any]:
        """Use Gemini API for enhanced analysis with cross-verification and contradiction detection."""
        try:
            # Initialize the LangChain Gemini model
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=GEMINI_API_KEY,
                temperature=0.2,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048
            )
            
            # Truncate text if too long
            if len(text) > 2000:
                text = text[:1997] + "..."
                
            # Create a more detailed prompt for Gemini with cross-verification data
            prompt = f"""
            Analyze the following text for potential misinformation. Focus on WORLDWIDE implications and cross-verification.
            
            Text to analyze:
            "{text}"
            """
            
            # Add source information if available
            if sources and len(sources) > 0:
                prompt += f"\n\nThe text references these sources:\n"
                for source in sources[:5]:  # Limit to 5 sources to keep prompt size reasonable
                    prompt += f"- {source}\n"
            
            # Add contradiction information if available
            if contradiction_data and len(contradiction_data) > 0:
                prompt += "\n\nThe following contradictions were detected between sources:\n"
                for i, (sources, details) in enumerate(list(contradiction_data.items())[:3]):  # Limit to top 3
                    prompt += f"{i+1}. Between {sources}: {details}\n"
            
            prompt += f"""
            Please provide a DETAILED analysis in JSON format with the following fields:
            1. misinformation_score: A number from 0 to 1 where 0 is highly credible and 1 is likely misinformation
            2. confidence: A number from 0 to 1 indicating your confidence in this assessment
            3. global_impact_score: A score from 0-1 indicating how significant this topic is globally
            4. detailed_analysis: A comprehensive analysis (at least 200 words) addressing:
            - Factual accuracy
            - Source credibility
            - Logical consistency
            - Global implications
            - Cross-verification results
            5. contradiction_assessment: Analysis of any contradictions between sources
            6. verification_sources: Suggested reliable sources to verify this information
            7. misinformation_indicators: A list of specific misinformation indicators found
            8. credibility_indicators: A list of specific credibility indicators found
            9. key_metrics: A JSON object with numeric metrics for dashboard display including:
            - emotional_language_score (0-1)
            - source_diversity_score (0-1)
            - factual_consistency_score (0-1)
            - global_spread_risk (0-1)
            - manipulation_probability (0-1)
            10. recommendations: Specific actions readers should take when encountering this information
            
            Your analysis should be thorough, unbiased, and focused on helping readers determine the reliability of this information.
            """
            
            # Make the API call using LangChain
            message = HumanMessage(content=prompt)
            response = llm.invoke([message])
            
            # Extract the text from the response
            text_response = response.content
            
            # Extract the JSON part from the response
            json_str = re.search(r'```json\s*(.*?)\s*```', text_response, re.DOTALL)
            if json_str:
                result = json.loads(json_str.group(1))
                return result
            
            # Try without markdown code blocks
            json_str = re.search(r'\{.*\}', text_response, re.DOTALL)
            if json_str:
                try:
                    result = json.loads(json_str.group(0))
                    return result
                except json.JSONDecodeError:
                    pass
            
            # Default values if we couldn't parse JSON
            return {
                "misinformation_score": 0.0,
                "confidence": 0.0,
                "detailed_analysis": "Could not extract structured analysis from API response.",
                "key_metrics": {
                    "emotional_language_score": 0.5,
                    "source_diversity_score": 0.5,
                    "factual_consistency_score": 0.5,
                    "global_spread_risk": 0.5,
                    "manipulation_probability": 0.5
                }
            }
            
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return empty dict on error
            return {}
    

    def cross_verify_sources(self, topic: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cross-verify multiple sources on the same topic to detect contradictions and consistency.
        
        Args:
            topic: The trending topic being analyzed
            articles: List of article dictionaries containing title, snippet, url, etc.
            
        Returns:
            Dictionary containing cross-verification results
        """
        if not articles or len(articles) < 2:
            return {
                "verification_possible": False,
                "reason": "Insufficient sources for cross-verification",
                "contradictions": {}
            }
        
        try:
            # Extract key information from articles
            article_info = []
            for i, article in enumerate(articles):
                snippet = article.get('snippet', '')
                title = article.get('title', '')
                url = article.get('url', '')
                domain = urllib.parse.urlparse(url).netloc if url else 'unknown'
                
                # Skip articles with insufficient content
                if not snippet and not title:
                    continue
                
                article_info.append({
                    "id": i,
                    "domain": domain,
                    "content": f"{title} {snippet}".strip(),
                    "url": url
                })
            
            # Need at least 2 articles with content
            if len(article_info) < 2:
                return {
                    "verification_possible": False,
                    "reason": "Insufficient content for cross-verification",
                    "contradictions": {}
                }
            
            # Compare each pair of articles for contradictions
            contradictions = {}
            similarities = {}
            fact_clusters = defaultdict(list)
            
            for a1, a2 in itertools.combinations(article_info, 2):
                # Calculate text similarity
                similarity = difflib.SequenceMatcher(None, a1["content"], a2["content"]).ratio()
                pair_key = f"{a1['domain']}-{a2['domain']}"
                similarities[pair_key] = similarity
                
                # If similar enough, consider them supporting each other
                if similarity > 0.6:
                    cluster_key = f"cluster_{hash(a1['content'][:50]) % 1000}"
                    fact_clusters[cluster_key].append(a1)
                    fact_clusters[cluster_key].append(a2)
                
                # Check for potential contradictions (empirically, very dissimilar articles on same topic
                # often have contradictory information)
                elif similarity < 0.3:
                    contradictions[pair_key] = {
                        "source1": a1["domain"],
                        "source2": a2["domain"],
                        "similarity": similarity,
                        "urls": [a1["url"], a2["url"]]
                    }
            
            # Deduplicate clusters
            for key in list(fact_clusters.keys()):
                fact_clusters[key] = list({item['id']: item for item in fact_clusters[key]}.values())
            
            # Calculate consistency metrics
            total_pairs = len(list(itertools.combinations(article_info, 2)))
            contradictory_pairs = len(contradictions)
            consistency_score = 1 - (contradictory_pairs / total_pairs) if total_pairs > 0 else 0
            
            # Group articles by shared information clusters
            cluster_sizes = [len(cluster) for cluster in fact_clusters.values()]
            largest_cluster_size = max(cluster_sizes) if cluster_sizes else 0
            largest_cluster_ratio = largest_cluster_size / len(article_info) if article_info else 0
            
            # Identify domains with multiple contradictions
            contradiction_counts = defaultdict(int)
            for pair_key in contradictions:
                domains = pair_key.split('-')
                contradiction_counts[domains[0]] += 1
                contradiction_counts[domains[1]] += 1
            
            problematic_sources = {
                domain: count for domain, count in contradiction_counts.items() 
                if count > len(article_info) * 0.3  # Sources contradicting >30% of others
            }
            
            return {
                "verification_possible": True,
                "contradictions": contradictions,
                "consistency_score": consistency_score,
                "fact_clusters": {key: [a["domain"] for a in items] for key, items in fact_clusters.items()},
                "largest_cluster_ratio": largest_cluster_ratio,
                "problematic_sources": problematic_sources,
                "article_count": len(article_info)
            }
            
        except Exception as e:
            logger.error(f"Error in cross-verification: {str(e)}")
            return {
                "verification_possible": False,
                "reason": f"Error during cross-verification: {str(e)}",
                "contradictions": {}
            }

    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze current global trends for misinformation with cross-verification and expanded Gemini analysis."""
        try:
            logger.info("Starting comprehensive worldwide misinformation analysis")
            
            # Get trends data - focus on GLOBAL trends
            trends_data = get_trending_topics()
            source_type = "real" if HAS_TRENDS_IMPORT else "mock"
            logger.info(f"Analyzing {len(trends_data)} global trends (using {source_type} data)")
            
            # Process each trend with enhanced analysis
            analyzed_trends = []
            overall_risk_score = 0
            total_contradictions = 0
            
            for trend in trends_data:
                topic = trend.get('topic', '')
                articles = trend.get('articles', [])
                
                # Skip empty trends
                if not topic and not articles:
                    continue
                
                # Extract sources for domain credibility analysis
                sources = []
                source_details = []
                for article in articles:
                    if 'url' in article and article['url']:
                        sources.append(article['url'])
                        domain = urllib.parse.urlparse(article['url']).netloc
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        
                        # Assess domain credibility
                        domain_cred = self._assess_domain_credibility(article['url'])
                        
                        source_details.append({
                            "title": article.get('title', 'Untitled'),
                            "url": article['url'],
                            "domain": domain,
                            "snippet": article.get('snippet', 'No description available'),
                            "is_credible": domain_cred.get('is_credible_source', False),
                            "is_problematic": domain_cred.get('is_problematic_source', False),
                            "credibility_score": 1 - domain_cred.get('score', 0.5)
                        })
                
                # Create a combined text from all articles
                combined_text = f"{topic}: "
                for article in articles:
                    if 'title' in article and article['title']:
                        combined_text += article['title'] + " "
                    if 'snippet' in article and article['snippet']:
                        combined_text += article['snippet'] + " "
                
                # NEW: Cross-verify sources
                cross_verification = self.cross_verify_sources(topic, articles)
                
                # NEW: Add contradiction data for Gemini
                contradiction_data = {
                    f"{details['source1']} and {details['source2']}": 
                    f"These sources disagree significantly (similarity score: {details['similarity']:.2f})"
                    for pair_key, details in cross_verification.get('contradictions', {}).items()
                }
                
                # Analyze the combined text with enhanced analysis including contradiction data
                analysis = self.analyze_text(combined_text, sources)
                
                # NEW: Get expanded Gemini analysis with cross-verification data
                gemini_analysis = None
                if HAS_GEMINI_API and len(combined_text) > 50:
                    try:
                        gemini_analysis = self._analyze_with_gemini(
                            combined_text, 
                            sources, 
                            contradiction_data
                        )
                        if gemini_analysis and "detailed_analysis" in gemini_analysis:
                            # Include the full Gemini analysis
                            analysis["gemini_detailed_analysis"] = gemini_analysis["detailed_analysis"]
                            analysis["gemini_contradiction_assessment"] = gemini_analysis.get("contradiction_assessment", "")
                            analysis["gemini_recommendations"] = gemini_analysis.get("recommendations", [])
                            analysis["gemini_verification_sources"] = gemini_analysis.get("verification_sources", [])
                            analysis["gemini_metrics"] = gemini_analysis.get("key_metrics", {})
                            
                            # Update scores if available
                            if "misinformation_score" in gemini_analysis:
                                # Blend scores, giving more weight to Gemini's assessment
                                analysis["misinformation_score"] = analysis["misinformation_score"] * 0.3 + gemini_analysis["misinformation_score"] * 0.7
                            
                            if "confidence" in gemini_analysis:
                                analysis["confidence"] = max(analysis["confidence"], gemini_analysis["confidence"])
                    except Exception as api_error:
                        logger.warning(f"Error using expanded Gemini API analysis: {str(api_error)}")
                
                risk_level = "low"
                if analysis["misinformation_score"] > 0.7:
                    risk_level = "high"
                elif analysis["misinformation_score"] > 0.4:
                    risk_level = "medium"
                
                # Count contradictions
                contradiction_count = len(cross_verification.get('contradictions', {}))
                total_contradictions += contradiction_count
                
                # Create enriched trend analysis
                analyzed_trend = {
                    "topic": topic,
                    "risk_level": risk_level,
                    "misinformation_score": analysis["misinformation_score"],
                    "confidence": analysis["confidence"],
                    "misinformation_indicators": analysis["misinformation_indicators"][:5],
                    "credibility_indicators": analysis["credibility_indicators"][:5],
                    "article_count": len(articles),
                    "justification": analysis["justification"],
                    "misinformation_categories": {k: v[:3] for k, v in analysis.get("misinformation_categories", {}).items()},
                    "has_gemini_analysis": "gemini_detailed_analysis" in analysis,
                    
                    # Add source details
                    "sources": source_details,
                    
                    # Add cross-verification data
                    "cross_verification": {
                        "contradiction_count": contradiction_count,
                        "consistency_score": cross_verification.get('consistency_score', 0),
                        "verification_possible": cross_verification.get('verification_possible', False),
                        "problematic_sources": cross_verification.get('problematic_sources', {}),
                        "contradictions": contradiction_data
                    },
                    
                    # Add metrics
                    "metrics": {
                        "credibility_score": 1 - analysis["misinformation_score"],
                        "confidence": analysis["confidence"],
                        "emotional_language": 0.5,
                        "source_reliability": 0.5,
                        "global_impact": gemini_analysis.get("global_impact_score", 0.5) if gemini_analysis else 0.5
                    }
                }
                
                # Add Gemini metrics if available
                if "gemini_metrics" in analysis:
                    analyzed_trend["metrics"].update({
                        "emotional_language": analysis["gemini_metrics"].get("emotional_language_score", 0.5),
                        "source_reliability": 1 - analysis["gemini_metrics"].get("manipulation_probability", 0.5),
                        "factual_consistency": analysis["gemini_metrics"].get("factual_consistency_score", 0.5),
                        "source_diversity": analysis["gemini_metrics"].get("source_diversity_score", 0.5),
                        "global_spread_risk": analysis["gemini_metrics"].get("global_spread_risk", 0.5)
                    })
                
                # Add Gemini analysis fields if available
                if "gemini_detailed_analysis" in analysis:
                    analyzed_trend["gemini_analysis"] = analysis["gemini_detailed_analysis"]
                
                if "gemini_contradiction_assessment" in analysis:
                    analyzed_trend["contradiction_assessment"] = analysis["gemini_contradiction_assessment"]
                
                if "gemini_recommendations" in analysis:
                    analyzed_trend["recommendations"] = analysis["gemini_recommendations"]
                
                if "gemini_verification_sources" in analysis:
                    analyzed_trend["verification_sources"] = analysis["gemini_verification_sources"]
                
                analyzed_trends.append(analyzed_trend)
                overall_risk_score += analysis["misinformation_score"]
            
            # Calculate overall statistics
            if analyzed_trends:
                overall_risk_score /= len(analyzed_trends)
            
            # Prepare summary text
            high_risk_count = sum(1 for t in analyzed_trends if t["risk_level"] == "high")
            medium_risk_count = sum(1 for t in analyzed_trends if t["risk_level"] == "medium")
            
            data_source_note = ""
            if not HAS_TRENDS_IMPORT:
                data_source_note = "Note: Using simulated trend data since the trends module could not be imported. "
            
            gemini_note = ""
            if HAS_GEMINI_API:
                gemini_note = "Enhanced with Gemini API for comprehensive global analysis. "
            
            # Enhanced summary focused on global implications
            concerning_trends = [t["topic"] for t in analyzed_trends if t["risk_level"] == "high"]
            concerning_trends_note = ""
            if concerning_trends:
                concerning_trends_note = f"Trends of global concern include: {', '.join(concerning_trends[:3])}"
                if len(concerning_trends) > 3:
                    concerning_trends_note += f" and {len(concerning_trends) - 3} others. "
                else:
                    concerning_trends_note += ". "
            
            # Add contradiction information
            contradiction_note = ""
            if total_contradictions > 0:
                contradiction_note = f"Detected {total_contradictions} significant contradictions between sources. "
                
            # Create detailed metrics summary for dashboard
            metrics_summary = {
                "topics_analyzed": len(analyzed_trends),
                "high_risk_percentage": (high_risk_count / len(analyzed_trends)) * 100 if analyzed_trends else 0,
                "overall_misinformation_score": overall_risk_score,
                "overall_confidence": sum(t["confidence"] for t in analyzed_trends) / len(analyzed_trends) if analyzed_trends else 0,
                "total_contradictions": total_contradictions,
                "analysis_timestamp": datetime.now().isoformat(),
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "average_misinformation_score": overall_risk_score,
                
                # Aggregate indicators across all trends
                "top_misinformation_indicators": self._aggregate_indicators(
                    [indicator for trend in analyzed_trends for indicator in trend.get("misinformation_indicators", [])]
                ),
                "top_credibility_indicators": self._aggregate_indicators(
                    [indicator for trend in analyzed_trends for indicator in trend.get("credibility_indicators", [])]
                ),
                
                # Add contradiction metrics
                "contradiction_metrics": {
                    "total": total_contradictions,
                    "per_topic_average": total_contradictions / len(analyzed_trends) if analyzed_trends else 0
                }
            }
            
            summary_text = (
                f"Global Misinformation Alert: Analyzed {len(analyzed_trends)} trending topics from worldwide sources.\n\n"
                f"Found {high_risk_count} high-risk topics and {medium_risk_count} medium-risk topics with potential for global impact. "
                f"{contradiction_note}The overall misinformation risk level is "
                f"{'high' if overall_risk_score > 0.7 else 'medium' if overall_risk_score > 0.4 else 'low'}. "
                f"{concerning_trends_note}\n\n"
                f"{data_source_note}{gemini_note}Our cross-verification system has compared multiple sources "
                f"for each topic to identify contradictions and verify consistency. "
                f"For each trend, we've provided a detailed global impact assessment and recommendations."
            )
            
            # Store and return results
            results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Global misinformation analysis completed",
                "analysis": summary_text,
                "trends": analyzed_trends,
                "overall_risk_score": overall_risk_score,
                "metrics_summary": metrics_summary,
                "using_lightweight_model": True,
                "using_mock_data": not HAS_TRENDS_IMPORT,
                "using_gemini_api": HAS_GEMINI_API
            }
            
            self.latest_results = results
            logger.info("Global misinformation trend analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in global misinformation analysis: {str(e)}")
            logger.error(traceback.format_exc())
            
            error_results = {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "message": f"Error in analysis: {str(e)}",
                "analysis": "The analysis encountered an error. Please check the server logs for details.",
                "using_lightweight_model": True,
                "error_details": str(e)
            }
            
            self.latest_results = error_results
            return error_results

    # Helper method to aggregate indicators
    def _aggregate_indicators(self, indicators):
        """Aggregate indicators and count frequencies."""
        if not indicators:
            return []
        
        # Count occurrences of each indicator
        counter = defaultdict(int)
        for indicator in indicators:
            counter[indicator] += 1
        
        # Convert to list of dictionaries sorted by count (descending)
        result = [{"name": name, "count": count} for name, count in counter.items()]
        return sorted(result, key=lambda x: x["count"], reverse=True)[:10]  # Top 10 only

    def get_latest_results(self) -> Dict[str, Any]:
        """Return the most recent analysis results.
        
        Returns:
            The latest analysis results or a default response if no results available
        """
        if self.latest_results is None:
            return {
                "success": False,
                "message": "No analysis has been performed yet",
                "timestamp": datetime.now().isoformat(),
                "using_lightweight_model": True
            }
        
        return self.latest_results

# Create a singleton instance
agent_service = LightweightMisinformationAgent()

# Provide main function for testing
if __name__ == "__main__":
    print("Testing enhanced lightweight misinformation agent...")
    results = agent_service.analyze_trends()
    print(json.dumps(results, indent=2))
