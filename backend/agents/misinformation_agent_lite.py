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

# Configure logging
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

# Define a fallback function for trends if import fails
def mock_get_trending_topics(num_trends=5):
    """Generate mock trending topics for testing when imports fail."""
    logger.warning("Using mock trend data since import failed")
    
    mock_topics = [
        "Global warming", "COVID-19 vaccine", "Political election", 
        "Economic recovery", "Celebrity scandal", "Technology innovation",
        "Sports championship", "Health study", "Education policy",
        "Environmental protection"
    ]
    
    mock_snippets = [
        "New research suggests significant impact on global populations.",
        "Officials released statements confirming the recent developments.",
        "Experts disagree on the long-term implications of this trend.",
        "Social media users have been sharing their opinions widely.",
        "The latest data shows surprising patterns that analysts are studying.",
        "Critics claim that misinformation is spreading about this topic."
    ]
    
    result = []
    for i in range(min(num_trends, len(mock_topics))):
        articles = []
        for j in range(3):  
            articles.append({
                "title": f"Article about {mock_topics[i]}",
                "snippet": random.choice(mock_snippets),
                "url": f"https://example.com/article{i}{j}"
            })
            
        result.append({
            "topic": mock_topics[i],
            "articles": articles,
            "volume": random.randint(1000, 50000),
            "started": datetime.now().isoformat()
        })
    
    return result

# Try to import trends utility
try:
    logger.info(f"Current working directory: {os.getcwd()}")
    from utils.trends import get_trending_topics
    HAS_TRENDS_IMPORT = True
    logger.info("Successfully imported get_trending_topics")
except ImportError:
    logger.error("Could not import trend utilities")
    get_trending_topics = mock_get_trending_topics
    HAS_TRENDS_IMPORT = False

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
GEMINI_API_KEY = "AIzaSyCpxZUOCicMaRgYxj0sBqespv0etbDMkH4"
HAS_GEMINI_API = GEMINI_API_KEY is not None and HAS_REQUESTS
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
    
    def _analyze_with_gemini(self, text: str) -> Dict[str, Any]:
        """Use Gemini API for enhanced analysis."""
        if not HAS_GEMINI_API or not HAS_REQUESTS:
            return {}
            
        try:
            # Use a content hash to avoid re-analyzing identical content
            content_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Truncate text if too long
            if len(text) > 1000:
                text = text[:997] + "..."
                
            # Prepare the prompt for Gemini
            prompt = f"""
            Please analyze the following text for potential misinformation indicators. 
            Consider factual accuracy, source credibility, logical consistency, and emotional manipulation.
            
            Text to analyze:
            "{text}"
            
            Provide your analysis in JSON format with the following fields:
            1. score: A number from 0 to 1 where 0 is highly credible and 1 is likely misinformation
            2. confidence: A number from 0 to 1 indicating your confidence in this assessment
            3. analysis: A brief analysis of the content
            4. indicators: A list of specific misinformation indicators found, if any
            5. justification: A brief explanation of your reasoning
            """
            
            # Make the API call
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            response = requests.post(
                f"{url}?key={GEMINI_API_KEY}",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                response_json = response.json()
                
                # Extract the text from the response
                if "candidates" in response_json and response_json["candidates"]:
                    text_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    
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
                        "score": 0.5,
                        "confidence": 0.3,
                        "analysis": "Could not extract structured analysis from API response.",
                        "justification": "Automated analysis was inconclusive."
                    }
            
            return {}
                
        except Exception as e:
            logger.error(f"Error in Gemini API analysis: {str(e)}")
            return {}
    
    def _find_related_trends(self, trends_data):
        """Find related trends based on content similarity."""
        if not trends_data or len(trends_data) < 2:
            return {}
            
        related_trends = {}
        
        # Extract text from each trend
        trend_texts = {}
        for i, trend in enumerate(trends_data):
            text = trend.get('topic', '') + " "
            articles = trend.get('articles', [])
            for article in articles:
                if 'title' in article and article['title']:
                    text += article['title'] + " "
                if 'snippet' in article and article['snippet']:
                    text += article['snippet'] + " "
            trend_texts[i] = text
        
        # Simple keyword overlap analysis
        for i in range(len(trends_data)):
            for j in range(i+1, len(trends_data)):
                # Skip if either trend is too short
                if len(trend_texts[i]) < 10 or len(trend_texts[j]) < 10:
                    continue
                
                # Calculate word overlap
                words_i = set(trend_texts[i].lower().split())
                words_j = set(trend_texts[j].lower().split())
                
                if len(words_i) == 0 or len(words_j) == 0:
                    continue
                
                overlap = len(words_i.intersection(words_j)) / min(len(words_i), len(words_j))
                
                # If sufficient overlap, consider them related
                if overlap > 0.2:  # 20% word overlap threshold
                    if i not in related_trends:
                        related_trends[i] = []
                    if j not in related_trends:
                        related_trends[j] = []
                    
                    related_trends[i].append((j, overlap))
                    related_trends[j].append((i, overlap))
        
        return related_trends
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze current trends for misinformation potential with enhanced analysis."""
        try:
            logger.info("Starting enhanced lightweight analysis of trends")
            
            # Get trends data
            trends_data = get_trending_topics()
            source_type = "real" if HAS_TRENDS_IMPORT else "mock"
            logger.info(f"Analyzing {len(trends_data)} trends (using {source_type} data)")
            
            # Process each trend
            analyzed_trends = []
            overall_risk_score = 0
            trend_topics = []
            
            # First pass - analyze each trend individually
            for trend in trends_data:
                topic = trend.get('topic', '')
                articles = trend.get('articles', [])
                
                # Skip empty trends
                if not topic and not articles:
                    continue
                
                trend_topics.append(topic)
                
                # Extract sources for domain credibility analysis
                sources = []
                for article in articles:
                    if 'url' in article and article['url']:
                        sources.append(article['url'])
                
                # Create a combined text from all articles
                combined_text = topic + " "
                for article in articles:
                    if 'title' in article and article['title']:
                        combined_text += article['title'] + " "
                    if 'snippet' in article and article['snippet']:
                        combined_text += article['snippet'] + " "
                
                # Analyze the combined text with enhanced analysis
                analysis = self.analyze_text(combined_text, sources)
                
                risk_level = "low"
                if analysis["misinformation_score"] > 0.7:
                    risk_level = "high"
                elif analysis["misinformation_score"] > 0.4:
                    risk_level = "medium"
                
                analyzed_trend = {
                    "topic": topic,
                    "risk_level": risk_level,
                    "misinformation_score": analysis["misinformation_score"],
                    "confidence": analysis["confidence"],
                    "misinformation_indicators": analysis["misinformation_indicators"][:5],  # Limit to top 5
                    "credibility_indicators": analysis["credibility_indicators"][:5],  # Limit to top 5
                    "article_count": len(articles),
                    "justification": analysis["justification"],
                    "misinformation_categories": {k: v[:3] for k, v in analysis.get("misinformation_categories", {}).items()},
                    "has_gemini_analysis": "gemini_analysis" in analysis
                }
                
                # Include Gemini analysis if available
                if "gemini_analysis" in analysis:
                    analyzed_trend["gemini_analysis"] = analysis["gemini_analysis"]
                
                analyzed_trends.append(analyzed_trend)
                overall_risk_score += analysis["misinformation_score"]
            
            # Second pass - find related trends
            related_trends = self._find_related_trends(trends_data)
            
            # Add relationship information to analyzed trends
            for i, trend_analysis in enumerate(analyzed_trends):
                if i in related_trends:
                    related_indices = [rel[0] for rel in related_trends[i]]
                    trend_analysis["related_trends"] = [analyzed_trends[idx]["topic"] for idx in related_indices]
            
            # Calculate overall statistics
            if analyzed_trends:
                overall_risk_score /= len(analyzed_trends)
            
            # Prepare summary text
            high_risk_count = sum(1 for t in analyzed_trends if t["risk_level"] == "high")
            medium_risk_count = sum(1 for t in analyzed_trends if t["risk_level"] == "medium")
            
            data_source_note = ""
            if not HAS_TRENDS_IMPORT:
                data_source_note = "Note: Using simulated trend data for analysis since the trends module could not be imported. "
            
            gemini_note = ""
            if HAS_GEMINI_API:
                gemini_note = "Enhanced with Gemini API analysis where applicable. "
            
            # Find trends with concerning patterns
            concerning_trends = [t["topic"] for t in analyzed_trends if t["risk_level"] == "high"]
            concerning_trends_note = ""
            if concerning_trends:
                concerning_trends_note = f"Trends of particular concern include: {', '.join(concerning_trends[:3])}"
                if len(concerning_trends) > 3:
                    concerning_trends_note += f" and {len(concerning_trends) - 3} others. "
                else:
                    concerning_trends_note += ". "
            
            summary_text = (
                f"Analyzed {len(analyzed_trends)} trending topics using enhanced misinformation detection.\n\n"
                f"Found {high_risk_count} high-risk topics and {medium_risk_count} medium-risk topics that "
                f"may contain misinformation. The overall misinformation risk level is "
                f"{'high' if overall_risk_score > 0.7 else 'medium' if overall_risk_score > 0.4 else 'low'}. "
                f"{concerning_trends_note}\n\n"
                f"{data_source_note}{gemini_note}This analysis was performed using a lightweight model optimized for systems with limited memory. "
                f"For each trend, we've provided a justification explaining why it received its risk score."
            )
            
            # Store and return results
            results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Enhanced lightweight analysis completed",
                "analysis": summary_text,
                "trends": analyzed_trends,
                "overall_risk_score": overall_risk_score,
                "using_lightweight_model": True,
                "using_mock_data": not HAS_TRENDS_IMPORT,
                "using_gemini_api": HAS_GEMINI_API
            }
            
            self.latest_results = results
            logger.info("Enhanced lightweight trend analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in enhanced lightweight trend analysis: {str(e)}")
            logger.error(traceback.format_exc())
            
            error_results = {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "message": f"Error in lightweight analysis: {str(e)}",
                "analysis": "The lightweight analysis encountered an error. Please check the server logs for details.",
                "using_lightweight_model": True,
                "error_details": str(e)
            }
            
            self.latest_results = error_results
            return error_results
    
    def get_latest_results(self) -> Dict[str, Any]:
        """Get the latest analysis results."""
        if not self.latest_results:
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "No analysis has been run yet",
                "analysis": "The lightweight agent hasn't analyzed any trends yet. Please trigger an analysis first.",
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
