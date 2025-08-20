from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# Load models once
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
nli_model = pipeline("text-classification", model="roberta-large-mnli")

def compute_similarity(claim, article_text):
    embeddings = embed_model.encode([claim, article_text], convert_to_tensor=True)
    score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
    return score

def check_entailment(claim, article_text):
    # NLI model: premise=article, hypothesis=claim
    result = nli_model(f"{article_text} </s></s> {claim}")[0]
    label = result['label'].lower()
    score = result['score']
    # Convert to numeric support score
    if "entailment" in label:
        return score
    elif "contradiction" in label:
        return -score
    else:
        return 0.0
