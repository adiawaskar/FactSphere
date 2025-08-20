import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_keywords(text, top_k=5):
    words = [w for w in text.split() if w not in ENGLISH_STOP_WORDS]
    return words[:top_k]
