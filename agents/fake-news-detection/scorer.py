# -------------------- scorer.py --------------------
def calculate_confidence(similarity_scores, entailment_scores):
    if not similarity_scores:
        return "UNVERIFIED", 0.0

    # Weighted average
    sim = sum(similarity_scores) / len(similarity_scores)
    ent = sum(entailment_scores) / len(entailment_scores) if entailment_scores else 0.0
    final_score = (0.6 * sim) + (0.4 * ent)

    # Threshold tuning
    if final_score > 0.45:  # lowered threshold
        return "VERIFIED", final_score
    elif final_score < -0.2:  # strong contradiction
        return "FAKE", abs(final_score)
    else:
        return "UNVERIFIED", abs(final_score)
