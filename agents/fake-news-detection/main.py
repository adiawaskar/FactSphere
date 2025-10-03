import json
import os
import sys
from urllib.parse import urlparse

from news_fetcher import fetch_news_for_claim
from text_utils import preprocess_text, extract_keywords, extract_claim_features, extract_contextual_keywords
from similarity_checker import best_evidence_for_claim
from evidence_evaluator import EvidenceEvaluator, decide_label_with_confidence

# ensure nltk punkt download if missing (silent)
try:
    import nltk
    nltk.download("punkt", quiet=True)
except Exception:
    pass

INPUT_FILE = "input_news.json"
OUTPUT_FILE = "output_result.json"

ALLOWLISTED_DOMAINS = [
    "nasa.gov", "who.int", "un.org", "dhs.gov", "reuters.com", "bbc.co.uk",
    "theguardian.com", "nytimes.com", "apnews.com", "timesofindia.indiatimes.com",
    "thehindu.com"
]

def _domain_of(url: str) -> str:
    try:
        net = urlparse(url).netloc or ""
        net = net.lower()
        if net.startswith("www."):
            net = net[4:]
        return net
    except Exception:
        return ""

def _is_allowlisted(url: str) -> bool:
    dom = _domain_of(url)
    for a in ALLOWLISTED_DOMAINS:
        if a in dom:
            return True
    return False

def decide_label_from_evidence(evidences):
    """
    evidences: list of tuples
      (combined_norm, bi_sim, cross_score, entail_score, sentence, url, source)
    combined_norm in [0,1]
    """
    if not evidences:
        return "UNVERIFIED", 0.0, "No evidence.", None

    combined, bi_sim, cross_score, entail_score, sent, url, source = evidences[0]
    # small allowlist boost
    boost = 0.08 if _is_allowlisted(url) else 0.0
    final = combined + boost
    # thresholds (tunable)
    if final >= 0.55:
        label = "REAL"
    elif final <= 0.25 and entail_score < -0.15:
        label = "FAKE"
    else:
        label = "UNVERIFIED"

    explanation = (
        f"Top evidence from {source} ({url}). Combined: {combined:.3f}, boost: {boost:.3f}, final: {final:.3f}. "
        f"(entail {entail_score:.3f}, bi_sim {bi_sim:.3f}, cross_raw {cross_score:.3f})"
    )

    evidence_details = {
        "evidence_sentence": sent,
        "evidence_url": url,
        "evidence_source": source,
        "combined": round(float(combined), 4),
        "bi_sim": round(float(bi_sim), 4),
        "cross_score": round(float(cross_score), 4),
        "entail_score": round(float(entail_score), 4),
        "final_with_boost": round(float(final), 4)
    }
    return label, float(final), explanation, evidence_details

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] {INPUT_FILE} missing.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        claims = json.load(f)

    evaluator = EvidenceEvaluator()
    results = []
    
    for claim in claims:
        title = (claim.get("title") or "").strip()
        source = (claim.get("source") or "").strip()
        content = (claim.get("content") or "").strip()
        full_claim = f"{title}. {content}".strip()
        
        if not full_claim:
            continue

        print(f"\n[CLAIM] {title}")
        
        # Enhanced feature extraction
        claim_features = extract_claim_features(full_claim)
        keywords = extract_contextual_keywords(full_claim)
        print(f"[DEBUG] Extracted entities: {[e['text'] for e in claim_features['entities'][:5]]}")
        print(f"[DEBUG] Keywords: {keywords[:5]}")

        # Fetch contextually relevant articles
        articles = fetch_news_for_claim(keywords, title=title, max_results=20, claim_text=content)
        print(f"[DEBUG] Fetched {len(articles)} contextually relevant articles")

        if not articles:
            label, confidence, explanation, evidence = "UNVERIFIED", 0.0, "No relevant articles found.", None
        else:
            # Evaluate each evidence piece
            evidence_evaluations = []
            for article in articles[:10]:  # Limit to top 10 most relevant
                # Split article into sentences for granular analysis
                sentences = article['content'].split('. ')[:5]  # Top 5 sentences
                
                for sentence in sentences:
                    if len(sentence.strip()) > 50:  # Skip short sentences
                        eval_result = evaluator.evaluate_claim_evidence_pair(
                            full_claim, sentence, article['url'], article['source']
                        )
                        evidence_evaluations.append(eval_result)
            
            label, confidence, explanation, evidence = decide_label_with_confidence(
                full_claim, evidence_evaluations
            )

        result = {
            "title": title,
            "source": source,
            "label": label,
            "confidence": round(float(confidence), 4),
            "explanation": explanation,
            "claim_features": {
                "entities": claim_features["entities"][:3],
                "sentiment": claim_features["sentiment"]["label"],
                "readability": claim_features["readability"]
            }
        }
        
        if evidence:
            result["evidence"] = {
                "sentence": evidence["evidence_sentence"][:200] + "...",
                "source": evidence["evidence_source"],
                "url": evidence["evidence_url"],
                "confidence_breakdown": {
                    "semantic_similarity": round(evidence["semantic_similarity"], 3),
                    "factual_consistency": round(evidence["factual_consistency"], 3),
                    "entity_overlap": round(evidence["entity_overlap"], 3),
                    "credibility_boost": round(evidence["credibility_boost"], 3)
                }
            }

        results.append(result)
        print(f"[RESULT] {label} (confidence: {confidence:.3f})")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\nAnalysis complete! Results saved to {OUTPUT_FILE}")
    print(f"Processed {len(results)} claims")

if __name__ == "__main__":
    main()
