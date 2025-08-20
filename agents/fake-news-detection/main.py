# import json
# from transformers import pipeline

# # Initialize the model
# MODEL = "jy46604790/Fake-News-Bert-Detect"
# classifier = pipeline("text-classification", model=MODEL, tokenizer=MODEL)

# # Mapping model labels to human-readable labels
# label_mapping = {
#     "LABEL_0": "REAL",
#     "LABEL_1": "FAKE"
# }

# # Load input news
# with open("input_news.json", "r", encoding="utf-8") as f:
#     news_list = json.load(f)

# results = []

# for news in news_list:
#     title = news.get("title", "")
#     source = news.get("source", "")
    
#     prediction = classifier(title)[0]  # returns {'label': 'LABEL_0' or 'LABEL_1', 'score': float}
#     human_label = label_mapping.get(prediction['label'], prediction['label'])

#     result = {
#         "title": title,
#         "source": source,
#         "label": human_label,
#         "confidence": prediction['score'],
#         "explanation": f"Predicted as {human_label} with confidence {prediction['score']:.2f}."
#     }
#     results.append(result)

# # Save results
# with open("output_result.json", "w", encoding="utf-8") as f:
#     json.dump(results, f, indent=4)

# print("Detection complete! Check output_result.json")

# main.py
# import json
# from transformers import pipeline

# # Initialize NLI model for fact-checking
# nli_model = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# # Trusted labels
# labels = ["REAL", "FAKE"]

# # Load input news
# with open("input_news.json", "r", encoding="utf-8") as f:
#     news_list = json.load(f)

# results = []

# # Optionally, add a small set of trusted summaries for reference (offline)
# trusted_sources = {
#     "NASA": "NASA provides reliable space and science news and research.",
#     "WHO": "World Health Organization provides factual updates on health and vaccines.",
#     "DHS": "Department of Homeland Security provides verified news on security issues."
# }

# for news in news_list:
#     title = news.get("title", "")
#     content = news.get("content", "")
#     combined_text = f"{title}. {content}"

#     # Include context from trusted sources if possible
#     context_text = " ".join(trusted_sources.values())

#     # Use zero-shot classification for verification
#     prediction = nli_model(combined_text, candidate_labels=labels, hypothesis_template="This claim is {}.")

#     # Pick the label with highest score
#     label = prediction['labels'][0]
#     confidence = prediction['scores'][0]

#     result = {
#         "title": title,
#         "source": news.get("source", ""),
#         "label": label,
#         "confidence": confidence,
#         "explanation": f"Predicted as {label} with confidence {confidence:.2f}. Claim checked against trusted knowledge."
#     }
#     results.append(result)

# # Save results
# with open("output_result.json", "w", encoding="utf-8") as f:
#     json.dump(results, f, indent=4)

# print("Detection complete! Check output_result.json")


# --------------------main.py--------------------
import json
from news_fetcher import fetch_news_for_claim
from text_utils import preprocess_text, extract_keywords
from similarity_checker import compute_similarity, check_entailment
from scorer import calculate_confidence

INPUT_FILE = "input_news.json"
OUTPUT_FILE = "output_result.json"

def main():
    # Load input claims
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        claims = json.load(f)

    results = []

    for claim in claims:
        title = claim.get("title", "")
        source = claim.get("source", "")
        content = claim.get("content", "")

        preprocessed_claim = preprocess_text(title + " " + content)
        keywords = extract_keywords(preprocessed_claim)

        # Fetch relevant news
        news_articles = fetch_news_for_claim(keywords)

        # Compute similarity and entailment
        similarity_scores = [compute_similarity(preprocessed_claim, a["content"]) for a in news_articles]
        entailment_scores = [check_entailment(preprocessed_claim, a["content"]) for a in news_articles]

        # Calculate final label and confidence
        label, confidence = calculate_confidence(similarity_scores, entailment_scores)

        explanation = f"Claim compared against {len(news_articles)} sources. Label: {label}, Confidence: {confidence:.2f}"

        results.append({
            "title": title,
            "source": source,
            "label": label,
            "confidence": confidence,
            "explanation": explanation
        })

    # Save results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print(f"Detection complete! Check {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
