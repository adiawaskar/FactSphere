# # import json
# # from transformers import pipeline

# # # Initialize the model
# # MODEL = "jy46604790/Fake-News-Bert-Detect"
# # classifier = pipeline("text-classification", model=MODEL, tokenizer=MODEL)

# # # Mapping model labels to human-readable labels
# # label_mapping = {
# #     "LABEL_0": "REAL",
# #     "LABEL_1": "FAKE"
# # }

# # # Load input news
# # with open("input_news.json", "r", encoding="utf-8") as f:
# #     news_list = json.load(f)

# # results = []

# # for news in news_list:
# #     title = news.get("title", "")
# #     source = news.get("source", "")
    
# #     prediction = classifier(title)[0]  # returns {'label': 'LABEL_0' or 'LABEL_1', 'score': float}
# #     human_label = label_mapping.get(prediction['label'], prediction['label'])

# #     result = {
# #         "title": title,
# #         "source": source,
# #         "label": human_label,
# #         "confidence": prediction['score'],
# #         "explanation": f"Predicted as {human_label} with confidence {prediction['score']:.2f}."
# #     }
# #     results.append(result)

# # # Save results
# # with open("output_result.json", "w", encoding="utf-8") as f:
# #     json.dump(results, f, indent=4)

# # print("Detection complete! Check output_result.json")

# # main.py
# # import json
# # from transformers import pipeline

# # # Initialize NLI model for fact-checking
# # nli_model = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# # # Trusted labels
# # labels = ["REAL", "FAKE"]

# # # Load input news
# # with open("input_news.json", "r", encoding="utf-8") as f:
# #     news_list = json.load(f)

# # results = []

# # # Optionally, add a small set of trusted summaries for reference (offline)
# # trusted_sources = {
# #     "NASA": "NASA provides reliable space and science news and research.",
# #     "WHO": "World Health Organization provides factual updates on health and vaccines.",
# #     "DHS": "Department of Homeland Security provides verified news on security issues."
# # }

# # for news in news_list:
# #     title = news.get("title", "")
# #     content = news.get("content", "")
# #     combined_text = f"{title}. {content}"

# #     # Include context from trusted sources if possible
# #     context_text = " ".join(trusted_sources.values())

# #     # Use zero-shot classification for verification
# #     prediction = nli_model(combined_text, candidate_labels=labels, hypothesis_template="This claim is {}.")

# #     # Pick the label with highest score
# #     label = prediction['labels'][0]
# #     confidence = prediction['scores'][0]

# #     result = {
# #         "title": title,
# #         "source": news.get("source", ""),
# #         "label": label,
# #         "confidence": confidence,
# #         "explanation": f"Predicted as {label} with confidence {confidence:.2f}. Claim checked against trusted knowledge."
# #     }
# #     results.append(result)

# # # Save results
# # with open("output_result.json", "w", encoding="utf-8") as f:
# #     json.dump(results, f, indent=4)

# # print("Detection complete! Check output_result.json")


# # -------------------- main.py --------------------
# # -------------------- main.py --------------------
# import json
# import os
# import sys
# from urllib.parse import urlparse

# from news_fetcher import fetch_news_for_claim
# from text_utils import preprocess_text, extract_keywords
# from similarity_checker import best_evidence_for_claim

# # ensure nltk punkt download if missing (silent)
# try:
#     import nltk
#     nltk.download("punkt", quiet=True)
# except Exception:
#     pass

# INPUT_FILE = "input_news.json"
# OUTPUT_FILE = "output_result.json"

# ALLOWLISTED_DOMAINS = [
#     "nasa.gov", "who.int", "un.org", "dhs.gov", "reuters.com", "bbc.co.uk",
#     "theguardian.com", "nytimes.com", "apnews.com", "timesofindia.indiatimes.com",
#     "thehindu.com"
# ]

# def _domain_of(url: str) -> str:
#     try:
#         net = urlparse(url).netloc or ""
#         net = net.lower()
#         if net.startswith("www."):
#             net = net[4:]
#         return net
#     except Exception:
#         return ""

# def _is_allowlisted(url: str) -> bool:
#     dom = _domain_of(url)
#     for a in ALLOWLISTED_DOMAINS:
#         if a in dom:
#             return True
#     return False

# def decide_label_from_evidence(evidences):
#     """
#     evidences: list of tuples
#       (combined_norm, bi_sim, cross_score, entail_score, sentence, url, source)
#     combined_norm in [0,1]
#     """
#     if not evidences:
#         return "UNVERIFIED", 0.0, "No evidence.", None

#     combined, bi_sim, cross_score, entail_score, sent, url, source = evidences[0]
#     # small allowlist boost
#     boost = 0.08 if _is_allowlisted(url) else 0.0
#     final = combined + boost
#     # thresholds (tunable)
#     if final >= 0.55:
#         label = "REAL"
#     elif final <= 0.25 and entail_score < -0.15:
#         label = "FAKE"
#     else:
#         label = "UNVERIFIED"

#     explanation = (
#         f"Top evidence from {source} ({url}). Combined: {combined:.3f}, boost: {boost:.3f}, final: {final:.3f}. "
#         f"(entail {entail_score:.3f}, bi_sim {bi_sim:.3f}, cross_raw {cross_score:.3f})"
#     )

#     evidence_details = {
#         "evidence_sentence": sent,
#         "evidence_url": url,
#         "evidence_source": source,
#         "combined": round(float(combined), 4),
#         "bi_sim": round(float(bi_sim), 4),
#         "cross_score": round(float(cross_score), 4),
#         "entail_score": round(float(entail_score), 4),
#         "final_with_boost": round(float(final), 4)
#     }
#     return label, float(final), explanation, evidence_details

# def main():
#     if not os.path.exists(INPUT_FILE):
#         print(f"[ERROR] {INPUT_FILE} missing.")
#         sys.exit(1)

#     with open(INPUT_FILE, "r", encoding="utf-8") as f:
#         claims = json.load(f)

#     results = []
#     for claim in claims:
#         title = (claim.get("title") or "").strip()
#         source = (claim.get("source") or "").strip()
#         content = (claim.get("content") or "").strip()
#         raw_claim = (title + " " + content).strip()
#         if not raw_claim:
#             continue

#         print(f"\n[CLAIM] {title}")
#         keywords = extract_keywords(preprocess_text(raw_claim))
#         print(f"[DEBUG] keywords: {keywords}")

#         articles = fetch_news_for_claim(keywords, title=title, max_results=25)
#         print(f"[DEBUG] fetched {len(articles)} articles")

#         if not articles:
#             label, confidence, explanation, evidence = "UNVERIFIED", 0.0, "No articles found.", None
#         else:
#             evidences = best_evidence_for_claim(raw_claim, articles, per_article_topk=2, global_topk=6)
#             print(f"[DEBUG] evidences: {len(evidences)}")
#             label, confidence, explanation, evidence = decide_label_from_evidence(evidences)

#         out = {
#             "title": title,
#             "source": source,
#             "label": label,
#             "confidence": round(float(confidence), 4),
#             "explanation": explanation
#         }
#         if evidence:
#             out["evidence"] = evidence

#         results.append(out)
#         print(f"[RESULT] {label} (conf {confidence:.3f})")
#         if evidence:
#             print(f"[EVID] {evidence['evidence_source']} - {evidence['evidence_sentence'][:160]}...")

#     with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=4, ensure_ascii=False)
#     print("\nDone. Output ->", OUTPUT_FILE)

# if __name__ == "__main__":
#     main()
import json
import os
import sys
from urllib.parse import urlparse

from news_fetcher import fetch_news_for_claim
from text_utils import preprocess_text, extract_keywords
from similarity_checker import best_evidence_for_claim

# for extracting article from URL
from newspaper import Article

try:
    import nltk
    nltk.download("punkt", quiet=True)
except Exception:
    pass

OUTPUT_FILE = "output_result.json"

ALLOWLISTED_DOMAINS = [
    "nasa.gov", "who.int", "un.org", "dhs.gov", "reuters.com", "bbc.co.uk",
    "bbc.com", "theguardian.com", "nytimes.com", "apnews.com",
    "timesofindia.indiatimes.com", "thehindu.com"
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
    if not evidences:
        return "UNVERIFIED", 0.0, "No evidence.", None

    combined, bi_sim, cross_score, entail_score, sent, url, source = evidences[0]
    boost = 0.08 if _is_allowlisted(url) else 0.0
    final = combined + boost

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

def extract_from_url(url: str):
    """Fetch article text and title from a given URL."""
    article = Article(url)
    article.download()
    article.parse()
    return article.title, article.text

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <news_url>")
        sys.exit(1)

    url = sys.argv[1]
    try:
        title, content = extract_from_url(url)
    except Exception as e:
        print(f"[ERROR] Could not extract article from {url}: {e}")
        sys.exit(1)

    raw_claim = (title + " " + content).strip()
    print(f"\n[CLAIM] {title}")
    keywords = extract_keywords(preprocess_text(raw_claim))
    print(f"[DEBUG] keywords: {keywords}")

    articles = fetch_news_for_claim(keywords, title=title, max_results=25)
    print(f"[DEBUG] fetched {len(articles)} articles")

    if not articles:
        label, confidence, explanation, evidence = "UNVERIFIED", 0.0, "No articles found.", None
    else:
        evidences = best_evidence_for_claim(raw_claim, articles, per_article_topk=2, global_topk=6)
        print(f"[DEBUG] evidences: {len(evidences)}")
        label, confidence, explanation, evidence = decide_label_from_evidence(evidences)

    result = {
        "title": title,
        "source": url,
        "label": label,
        "confidence": round(float(confidence), 4),
        "explanation": explanation
    }
    if evidence:
        result["evidence"] = evidence

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump([result], f, indent=4, ensure_ascii=False)

    print(f"[RESULT] {label} (conf {confidence:.3f})")
    if evidence:
        print(f"[EVID] {evidence['evidence_source']} - {evidence['evidence_sentence'][:160]}...")
    print("\nDone. Output ->", OUTPUT_FILE)

if __name__ == "__main__":
    main()