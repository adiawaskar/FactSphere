# -------------------- text_utils.py --------------------
import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def preprocess_text(text):
    text = (text or "").lower()
    # Keep hyphens/colons because they often appear in names/dates
    text = re.sub(r"[^a-z0-9\s\-:]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_keywords(text, top_k=6):
    words = [w for w in (text or "").split() if w not in ENGLISH_STOP_WORDS and len(w) > 2]
    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for w in words:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq[:top_k]
