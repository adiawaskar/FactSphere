# -------------------- text_utils.py --------------------
#agents/fake-news-detection/text_utils.py
import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import spacy
from textstat import flesch_reading_ease
from transformers import pipeline

nlp = spacy.load("en_core_web_sm")
sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

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

def extract_claim_features(text):
    """Extract comprehensive features from claim text"""
    doc = nlp(text)
    
    features = {
        "entities": [],
        "key_phrases": [],
        "sentiment": None,
        "readability": flesch_reading_ease(text),
        "question_words": [],
        "temporal_indicators": [],
        "certainty_indicators": []
    }
    
    # Extract entities
    for ent in doc.ents:
        features["entities"].append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        })
    
    # Extract noun phrases as key concepts
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 3:  # Keep short phrases
            features["key_phrases"].append(chunk.text)
    
    # Sentiment analysis
    try:
        sentiment_result = sentiment_analyzer(text[:512])  # Limit for model
        features["sentiment"] = sentiment_result[0]
    except:
        features["sentiment"] = {"label": "NEUTRAL", "score": 0.5}
    
    # Question words and temporal indicators
    question_words = ["how", "what", "when", "where", "why", "who"]
    temporal_words = ["yesterday", "today", "tomorrow", "recently", "now", "soon"]
    certainty_words = ["definitely", "certainly", "possibly", "maybe", "allegedly"]
    
    text_lower = text.lower()
    features["question_words"] = [w for w in question_words if w in text_lower]
    features["temporal_indicators"] = [w for w in temporal_words if w in text_lower]
    features["certainty_indicators"] = [w for w in certainty_words if w in text_lower]
    
    return features

def extract_contextual_keywords(text, top_k=8):
    """Extract contextually relevant keywords using NER and noun chunks"""
    doc = nlp(text)
    keywords = []
    
    # Priority 1: Named entities (people, organizations, places)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT"] and len(ent.text) > 2:
            keywords.append(ent.text)
    
    # Priority 2: Important noun phrases
    for chunk in doc.noun_chunks:
        if 2 <= len(chunk.text.split()) <= 3:
            keywords.append(chunk.text)
    
    # Priority 3: Key single words (excluding stop words)
    words = [token.lemma_.lower() for token in doc 
             if not token.is_stop and not token.is_punct 
             and len(token.text) > 3 and token.pos_ in ["NOUN", "ADJ", "VERB"]]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords + words:
        if keyword.lower() not in seen:
            seen.add(keyword.lower())
            unique_keywords.append(keyword)
    
    return unique_keywords[:top_k]
