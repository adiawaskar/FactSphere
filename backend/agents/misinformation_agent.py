import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Update imports to use langchain_community instead of langchain
from langchain.agents import AgentExecutor, AgentType, initialize_agent, Tool
from langchain_community.llms import HuggingFaceHub
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks import StdOutCallbackHandler
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Optional imports with fallback handling
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logging.warning("newspaper3k module not available. Article extraction will be limited.")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logging.warning("BeautifulSoup module not available. HTML parsing will be limited.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests module not available. Web requests will be limited.")

try:
    import nltk
    NLTK_AVAILABLE = True
    # Download necessary NLTK data
    try:
        nltk.download('punkt', quiet=True)
    except Exception as e:
        logging.warning(f"Failed to download NLTK data: {e}")
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK module not available. Text processing will be limited.")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas module not available. Data analysis will be limited.")

try:
    from transformers import pipeline
    from huggingface_hub import login
    TRANSFORMERS_AVAILABLE = True
    
    # Initialize Hugging Face API token
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
    if HUGGINGFACE_API_TOKEN:
        login(HUGGINGFACE_API_TOKEN)
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers module not available. NLP capabilities will be limited.")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("misinformation-agent")


class MisinformationAnalysisTool:
    """Tool for analyzing content for potential misinformation."""
    
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        self.zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        
    def extract_article_content(self, url: str) -> str:
        """Extract the content of an article from its URL using newspaper3k."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            logger.error(f"Error extracting article content: {e}")
            return ""
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze the sentiment of text content."""
        try:
            if not text:
                return {"label": "NEUTRAL", "score": 0.5}
            
            # Truncate text if it's too long
            truncated_text = text[:1000]
            result = self.sentiment_analyzer(truncated_text)[0]
            return result
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"label": "NEUTRAL", "score": 0.5}
    
    def classify_misinformation(self, text: str) -> Dict[str, Any]:
        """Classify text for potential misinformation indicators."""
        try:
            if not text:
                return {
                    "labels": ["factual", "misleading", "false"],
                    "scores": [0.33, 0.33, 0.33]
                }
            
            # Truncate text if it's too long
            truncated_text = text[:1000]
            
            result = self.zero_shot_classifier(
                truncated_text,
                candidate_labels=["factual", "misleading", "false"],
            )
            
            return {
                "labels": result["labels"],
                "scores": result["scores"]
            }
        except Exception as e:
            logger.error(f"Error classifying misinformation: {e}")
            return {
                "labels": ["factual", "misleading", "false"],
                "scores": [0.33, 0.33, 0.33]
            }
    
    def analyze_content(self, url_or_text: str) -> Dict[str, Any]:
        """Analyze content for misinformation indicators."""
        try:
            # Determine if input is URL or text
            if url_or_text.startswith(('http://', 'https://')):
                text = self.extract_article_content(url_or_text)
                source_type = "url"
                source = url_or_text
            else:
                text = url_or_text
                source_type = "text"
                source = "direct input"
            
            # Analyze text
            sentiment = self.analyze_sentiment(text)
            classification = self.classify_misinformation(text)
            
            # Determine misinformation risk level
            risk_score = classification["scores"][1] * 0.5 + classification["scores"][2] * 1.0
            
            if risk_score > 0.6:
                risk_level = "high"
            elif risk_score > 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # Prepare result
            result = {
                "source": source,
                "source_type": source_type,
                "sentiment": {
                    "label": sentiment["label"],
                    "score": sentiment["score"]
                },
                "classification": {
                    "labels": classification["labels"],
                    "scores": classification["scores"]
                },
                "misinformation_risk": {
                    "score": risk_score,
                    "level": risk_level
                },
                "text_snippet": text[:300] + "..." if len(text) > 300 else text
            }
            
            return result
        except Exception as e:
            logger.error(f"Error in analyze_content: {e}")
            return {
                "source": url_or_text,
                "error": str(e),
                "misinformation_risk": {
                    "level": "unknown"
                }
            }


class TrendAnalysisTool:
    """Tool for analyzing social media and news trends."""
    
    def __init__(self):
        from ..utils.trends import get_trending_topics
        self.get_trending_topics = get_trending_topics
        self.analysis_tool = MisinformationAnalysisTool()
    
    def get_trends(self, geo: str = 'IN') -> List[Dict[str, Any]]:
        """Get current trending topics."""
        try:
            return self.get_trending_topics(geo)
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            return []
    
    def analyze_trend(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single trend for misinformation indicators."""
        try:
            topic = trend.get('topic', '')
            articles = trend.get('articles', [])
            
            # Analyze each article
            article_analyses = []
            for article in articles:
                if 'url' in article:
                    analysis = self.analysis_tool.analyze_content(article['url'])
                    analysis['article_title'] = article.get('title', '')
                    analysis['article_source'] = article.get('source', '')
                    article_analyses.append(analysis)
            
            # Calculate overall risk score
            if article_analyses:
                risk_scores = [a['misinformation_risk']['score'] for a in article_analyses 
                              if 'misinformation_risk' in a and 'score' in a['misinformation_risk']]
                avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.5
                
                if avg_risk_score > 0.6:
                    overall_risk = "high"
                elif avg_risk_score > 0.3:
                    overall_risk = "medium"
                else:
                    overall_risk = "low"
            else:
                avg_risk_score = 0.5
                overall_risk = "medium"
            
            # Prepare result
            result = {
                "topic": topic,
                "articles_analyzed": len(article_analyses),
                "misinformation_risk": {
                    "score": avg_risk_score,
                    "level": overall_risk
                },
                "article_analyses": article_analyses
            }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return {
                "topic": trend.get('topic', 'Unknown'),
                "error": str(e),
                "misinformation_risk": {
                    "level": "unknown"
                }
            }
    
    def analyze_all_trends(self) -> List[Dict[str, Any]]:
        """Get and analyze all current trends."""
        try:
            trends = self.get_trends()
            
            if not trends:
                logger.warning("No trends retrieved")
                return []
            
            logger.info(f"Analyzing {len(trends)} trends...")
            analyzed_trends = []
            
            for trend in trends:
                analysis = self.analyze_trend(trend)
                analyzed_trends.append(analysis)
                logger.info(f"Analyzed trend: {trend.get('topic', 'Unknown')}")
            
            return analyzed_trends
        except Exception as e:
            logger.error(f"Error analyzing all trends: {e}")
            return []


def create_misinformation_agent():
    """Create and configure the misinformation analysis agent."""
    try:
        # Initialize tools
        search_tool = DuckDuckGoSearchRun()
        analysis_tool = MisinformationAnalysisTool()
        trend_tool = TrendAnalysisTool()
        
        # Define tools for the agent
        tools = [
            Tool(
                name="Search",
                func=search_tool.run,
                description="Useful for searching the web for current information and news articles."
            ),
            Tool(
                name="AnalyzeContent",
                func=analysis_tool.analyze_content,
                description="Analyzes a URL or text for misinformation indicators. Input should be a URL or text content."
            ),
            Tool(
                name="GetTrends",
                func=trend_tool.get_trends,
                description="Gets current trending topics. Optional input: geo code (e.g., 'US', 'IN')."
            ),
            Tool(
                name="AnalyzeTrend",
                func=trend_tool.analyze_trend,
                description="Analyzes a single trend for misinformation. Input should be a trend object."
            ),
            Tool(
                name="AnalyzeAllTrends",
                func=trend_tool.analyze_all_trends,
                description="Gets and analyzes all current trending topics."
            )
        ]
        
        # Initialize language model
        llm = HuggingFaceHub(
            repo_id="google/flan-t5-large",
            model_kwargs={"temperature": 0.5, "max_length": 512}
        )
        
        # Create memory for the agent
        memory = ConversationBufferMemory(memory_key="chat_history")
        
        # Initialize the agent
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            handle_parsing_errors=True
        )
        
        return agent
    except Exception as e:
        logger.error(f"Error creating misinformation agent: {e}")
        raise


class MisinformationAgentService:
    """Service for running the misinformation agent and storing results."""
    
    def __init__(self):
        self.agent = None
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_results")
        os.makedirs(self.results_dir, exist_ok=True)
        self.latest_results = None
    
    def initialize_agent(self):
        """Initialize the agent if not already initialized."""
        if self.agent is None:
            try:
                logger.info("Initializing misinformation agent...")
                self.agent = create_misinformation_agent()
                logger.info("Agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                raise
    
    def run_agent(self, query: str = "Analyze current trends for misinformation") -> Dict[str, Any]:
        """Run the agent with a specific query."""
        try:
            self.initialize_agent()
            
            logger.info(f"Running agent with query: {query}")
            result = self.agent.run(query)
            
            # Process and store result
            processed_result = self._process_result(result)
            self._store_result(processed_result)
            
            self.latest_results = processed_result
            return processed_result
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "query": query
            }
            self.latest_results = error_result
            return error_result
    
    def _process_result(self, raw_result: str) -> Dict[str, Any]:
        """Process the raw result from the agent."""
        try:
            # Try to parse as JSON if possible
            try:
                parsed_json = json.loads(raw_result)
                processed_result = parsed_json
            except json.JSONDecodeError:
                # Not JSON, treat as text
                processed_result = {"analysis": raw_result}
            
            # Add metadata
            processed_result["timestamp"] = datetime.now().isoformat()
            processed_result["success"] = True
            
            return processed_result
        except Exception as e:
            logger.error(f"Error processing agent result: {e}")
            return {
                "success": False,
                "error": str(e),
                "raw_result": raw_result,
                "timestamp": datetime.now().isoformat()
            }
    
    def _store_result(self, result: Dict[str, Any]):
        """Store the processed result."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.results_dir, f"agent_analysis_{timestamp}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Stored agent result to {filename}")
        except Exception as e:
            logger.error(f"Error storing agent result: {e}")
    
    def get_latest_results(self) -> Optional[Dict[str, Any]]:
        """Get the latest agent results."""
        if self.latest_results:
            return self.latest_results
        
        # If no results in memory, try to load the most recent file
        try:
            files = [f for f in os.listdir(self.results_dir) if f.startswith("agent_analysis_")]
            if not files:
                return None
            
            latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(self.results_dir, x)))
            with open(os.path.join(self.results_dir, latest_file), 'r', encoding='utf-8') as f:
                self.latest_results = json.load(f)
            
            return self.latest_results
        except Exception as e:
            logger.error(f"Error getting latest results: {e}")
            return None
    
    def analyze_trends(self) -> Dict[str, Any]:
        """Analyze current trends for misinformation."""
        return self.run_agent("Analyze the current trending topics for misinformation. Provide a detailed analysis of each trend, including risk level, potential false narratives, and credibility assessment.")


# Singleton instance
agent_service = MisinformationAgentService()


if(__name__ == "__main__"):
    agent_service.run_agent("Test query")