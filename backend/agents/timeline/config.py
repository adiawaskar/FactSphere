# agents/timeline/config.py
import os
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables from .env file
load_dotenv()

# --- API Keys & Credentials ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# --- LLM Models ---
LLM_SMART_MODEL = 'gemini-2.5-flash'

# --- Vector Store Settings ---
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "news_articles"
DISTANCE_THRESHOLD = 0.1 

# --- Agent Loop Settings ---
MAX_ITERATIONS = 2          # How many "curiosity loops" to run
MAX_ARTICLES_PER_STEP = 3   # Articles to fetch per query per iteration

# --- Global Objects ---
CONSOLE = Console()