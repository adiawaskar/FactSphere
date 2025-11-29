# # agents/bias_analyzer_priyank/config.py
# import os
# from dotenv import load_dotenv
# from rich.console import Console

# # Load environment variables from .env file
# load_dotenv()

# # --- API Keys ---
# # Remove or comment out the old Groq key
# # GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # <-- Added
# GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

# # --- LLM Models ---
# # Updated model names for Google Gemini
# LLM_FAST_MODEL = 'gemini-2.5-flash' # <-- Updated
# LLM_SMART_MODEL = 'gemini-2.5-flash' # <-- Updated
# # LLM_SMART_MODEL = 'gemini-1.5-pro-latest'   # <-- Updated

# # --- Knowledge Base Settings ---
# EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
# CHROMA_DB_PATH = "neutral_knowledge_base"
# COLLECTION_NAME = "neutral_articles"

# # --- Bias Analysis ---
# # Articles with a final score between these values are considered "Neutral / Balanced".
# NEUTRAL_BIAS_THRESHOLD = 0.1

# # --- Global Objects ---
# # A single console object for consistent output styling.
# CONSOLE = Console()

# agents/bias_analyzer_priyank/config.py
import os
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY") # Required for the new news_fetcher

# --- LLM Models ---
# The 'models/' prefix is often required by the Google GenAI SDK
LLM_FAST_MODEL = 'models/gemini-2.5-flash'  # Fast and efficient
LLM_SMART_MODEL = 'models/gemini-2.5-pro'   # More capable for complex reasoning

# If 'pro' fails for you, uncomment the line below:
# LLM_SMART_MODEL = 'models/gemini-2.5-flash'

# --- Knowledge Base Settings ---
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CHROMA_DB_PATH = "neutral_knowledge_base"
COLLECTION_NAME = "neutral_articles"

# --- Search Settings ---
# These are new and required by the updated fetcher
SEARCH_TIMEOUT = 15
MAX_CONTENT_LENGTH = 8000

# --- Bias Analysis ---
NEUTRAL_BIAS_THRESHOLD = 0.1

# --- Global Objects ---
CONSOLE = Console()