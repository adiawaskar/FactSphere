import os
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- LLM Models ---
# Used for enhancing search queries and generating misconceptions.
LLM_FAST_MODEL = 'llama3-8b-8192'
# A more powerful model for the final fact-checking report.
LLM_SMART_MODEL = 'llama3-70b-8192'

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