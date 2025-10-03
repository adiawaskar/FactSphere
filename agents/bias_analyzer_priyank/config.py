# agents/bias_analyzer_priyank/config.py
import os
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
# Remove or comment out the old Groq key
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # <-- Added
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

# --- LLM Models ---
# Updated model names for Google Gemini
LLM_FAST_MODEL = 'gemini-1.5-flash-latest' # <-- Updated
LLM_SMART_MODEL = 'gemini-1.5-flash-latest' # <-- Updated
# LLM_SMART_MODEL = 'gemini-1.5-pro-latest'   # <-- Updated

# --- Knowledge Base Settings ---
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CHROMA_DB_PATH = "neutral_knowledge_base"
COLLECTION_NAME = "neutral_articles"

# --- Bias Analysis ---
# Articles with a final score between these values are considered "Neutral / Balanced".
NEUTRAL_BIAS_THRESHOLD = 0.1

# --- Global Objects ---
# A single console object for consistent output styling.
CONSOLE = Console()