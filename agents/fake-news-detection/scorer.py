def calculate_confidence(similarity_scores, entailment_scores):
    if not similarity_scores:
        return "FAKE", 0.0
    avg_similarity = sum(similarity_scores) / len(similarity_scores)
    avg_entailment = sum(entailment_scores) / len(entailment_scores)

    # Weighted scoring
    final_score = 0.6 * avg_similarity + 0.4 * max(0.0, avg_entailment)

    label = "REAL" if final_score > 0.5 else "FAKE"
    return label, final_score
