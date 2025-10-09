# -------------------- similarity_checker.py --------------------
#agents/fake-news-detection/similarity_checker.py
import re
import math
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from transformers import pipeline

# Models
BI_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # compact and effective

embed_model = SentenceTransformer(BI_MODEL)
cross_encoder = CrossEncoder(CROSS_MODEL)

# NLI pipeline (robust unwrap)
nli_pipeline = pipeline("text-classification", model="roberta-large-mnli", truncation=True, top_k=None)


def _sigmoid(x):
    try:
        return 1.0 / (1.0 + math.exp(-float(x)))
    except Exception:
        return 0.5


def _normalize_bi(bi):
    # bi is cosine in [-1,1] -> map to [0,1]
    try:
        return float((bi + 1.0) / 2.0)
    except Exception:
        return 0.5


def _normalize_entail(entail):
    # entail roughly in [-1,1] (entail-contradiction) -> map to [0,1]
    try:
        return float((entail + 1.0) / 2.0)
    except Exception:
        return 0.5


def _nli_support_score(claim, sentence):
    outputs = nli_pipeline({"text": sentence, "text_pair": claim})
    # unwrap nested lists
    if isinstance(outputs, list) and outputs and isinstance(outputs[0], list):
        outputs = outputs[0]
    # defensive: ensure we have list of dicts
    if not isinstance(outputs, list):
        return 0.0
    label_scores = {o.get("label", "").upper(): o.get("score", 0.0) for o in outputs}
    if "LABEL_0" in label_scores:
        entail = label_scores.get("LABEL_2", 0.0)
        contra = label_scores.get("LABEL_0", 0.0)
    else:
        entail = label_scores.get("ENTAILMENT", 0.0)
        contra = label_scores.get("CONTRADICTION", 0.0)
    try:
        return float(entail - contra)
    except Exception:
        return 0.0


def rerank_claim_sentence_pairs(claim, candidate_sentences, top_k=20, prefilter_keywords=None):
    """
    1) Filter candidate_sentences by length and keyword overlap (prefilter_keywords)
    2) Use bi-encoder to get similarity, keep top N (60)
    3) Use cross-encoder to rerank the top candidates
    Returns list of tuples (sentence, bi_sim, cross_score)
    """
    if not candidate_sentences:
        return []

    # Pre-filter sentences: length and keyword overlap
    filtered = []
    for s in candidate_sentences:
        if not s or len(s.split()) < 7:
            continue
        if prefilter_keywords:
            s_low = s.lower()
            if not any(kw in s_low for kw in prefilter_keywords):
                continue
        filtered.append(s)
    if not filtered:
        return []

    # Bi-encoder sims
    claim_emb = embed_model.encode(claim, convert_to_tensor=True, normalize_embeddings=True)
    sent_embs = embed_model.encode(filtered, convert_to_tensor=True, normalize_embeddings=True)
    bi_sims = util.cos_sim(claim_emb, sent_embs)[0].cpu().tolist()

    # keep top M by bi-sim to limit cross-encoder calls
    M = min(len(bi_sims), 60)
    top_idx = sorted(range(len(bi_sims)), key=lambda i: bi_sims[i], reverse=True)[:M]

    pairs = [(filtered[i], bi_sims[i]) for i in top_idx]
    cross_inputs = [(claim, s) for s, _ in pairs]

    # Cross-encoder scores (higher = more relevant)
    try:
        cross_scores = cross_encoder.predict(cross_inputs, convert_to_numpy=True).tolist()
    except Exception:
        # If cross-encoder fails for any reason, fall back to bi scores
        cross_scores = [float(b) for _, b in pairs]

    reranked = []
    for (s, bi), cs in zip(pairs, cross_scores):
        reranked.append((s, float(bi), float(cs)))

    # sort by cross_score desc
    reranked.sort(key=lambda x: x[2], reverse=True)
    return reranked[:top_k]


def best_evidence_for_claim(claim, articles, per_article_topk=2, global_topk=6):
    """
    For each article, split into sentences, accumulate candidates across articles,
    rerank with cross-encoder, compute NLI, normalize signals and return top evidences.

    Returns list of tuples:
      (combined_norm, bi_sim, cross_score, entail_score, sentence, url, source)
    where combined_norm is in [0,1].
    """
    # print(articles)
    # Simple claim keyword set for prefiltering (words length>3)
    claim_tokens = set(re.findall(r"\w{4,}", claim.lower()))

    # collect sentences and metadata
    article_sentences = []
    for art in articles:
        txt = (art.get("content") or "").strip()
        if not txt:
            continue
        # naive sentence split
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", txt) if s.strip()]
        # keep a reasonable number per article to control cost
        for s in sents[:80]:
            article_sentences.append((s, art.get("url", ""), art.get("source", "")))

    if not article_sentences:
        return []

    sentences = [t[0] for t in article_sentences]

    # Rerank claim vs sentences (bi -> cross)
    reranked = rerank_claim_sentence_pairs(
        claim,
        sentences,
        top_k=max(global_topk * per_article_topk, 40),
        prefilter_keywords=claim_tokens
    )

    if not reranked:
        return []

    evidences = []
    # For top reranked sentences, compute NLI and normalized features
    for s, bi, cross in reranked:
        # find original article metadata
        try:
            idx = sentences.index(s)
        except ValueError:
            idx = None
        url = article_sentences[idx][1] if idx is not None else ""
        source = article_sentences[idx][2] if idx is not None else ""

        entail = _nli_support_score(claim, s)

        # normalize signals
        cross_sig = _sigmoid(cross)               # (0,1)
        bi_norm = _normalize_bi(bi)              # (0,1)
        ent_norm = _normalize_entail(entail)     # (0,1)

        # Weighted combine (normalized space)
        combined = 0.6 * cross_sig + 0.25 * bi_norm + 0.15 * ent_norm

        evidences.append((float(combined), float(bi), float(cross), float(entail), s, url, source))

    # sort by combined descending and return top global_topk
    evidences.sort(key=lambda x: x[0], reverse=True)
    return evidences[:global_topk]
