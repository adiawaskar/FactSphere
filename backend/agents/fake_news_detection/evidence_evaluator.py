import numpy as np
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import spacy

class EvidenceEvaluator:
    def __init__(self):
        self.nli_model = pipeline("zero-shot-classification", 
                                 model="facebook/bart-large-mnli")
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load("en_core_web_sm")
        
    def evaluate_claim_evidence_pair(self, claim, evidence_sentence, evidence_url="", evidence_source=""):
        """Comprehensive evaluation of claim against evidence"""
        
        # 1. Semantic similarity
        semantic_score = self._semantic_similarity(claim, evidence_sentence)
        
        # 2. Factual consistency check
        consistency_score = self._factual_consistency(claim, evidence_sentence)
        
        # 3. Entity overlap analysis
        entity_score = self._entity_overlap(claim, evidence_sentence)
        
        # 4. Contradiction detection
        contradiction_score = self._detect_contradiction(claim, evidence_sentence)
        
        # 5. Source credibility boost
        credibility_boost = self._source_credibility_score(evidence_url, evidence_source)
        
        # Weighted combination
        final_score = (
            semantic_score * 0.3 +
            consistency_score * 0.4 +
            entity_score * 0.2 +
            (1 - contradiction_score) * 0.1 +
            credibility_boost
        )
        
        return {
            "final_score": final_score,
            "semantic_similarity": semantic_score,
            "factual_consistency": consistency_score,
            "entity_overlap": entity_score,
            "contradiction_detected": contradiction_score > 0.7,
            "credibility_boost": credibility_boost,
            "evidence_sentence": evidence_sentence,
            "evidence_url": evidence_url,
            "evidence_source": evidence_source
        }
    
    def _semantic_similarity(self, claim, evidence):
        """Calculate semantic similarity using sentence transformers"""
        embeddings = self.sentence_model.encode([claim, evidence])
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        return max(0, similarity)
    
    def _factual_consistency(self, claim, evidence):
        """Check if evidence supports, contradicts, or is neutral to claim"""
        try:
            result = self.nli_model(evidence, [claim])
            # Assuming the model returns entailment, contradiction, neutral
            scores = result['scores']
            labels = result['labels']
            
            entailment_idx = labels.index('entailment') if 'entailment' in labels else 0
            return scores[entailment_idx]
        except:
            return 0.5
    
    def _entity_overlap(self, claim, evidence):
        """Calculate overlap of named entities"""
        claim_doc = self.nlp(claim)
        evidence_doc = self.nlp(evidence)
        
        claim_entities = set(ent.text.lower() for ent in claim_doc.ents)
        evidence_entities = set(ent.text.lower() for ent in evidence_doc.ents)
        
        if not claim_entities:
            return 0.5
        
        overlap = len(claim_entities.intersection(evidence_entities))
        return overlap / len(claim_entities)
    
    def _detect_contradiction(self, claim, evidence):
        """Detect if evidence contradicts the claim"""
        try:
            # Check for contradictory patterns
            contradictory_phrases = [
                ("is", "is not"), ("are", "are not"), ("has", "has not"),
                ("will", "will not"), ("can", "cannot"), ("true", "false"),
                ("confirmed", "denied"), ("supports", "opposes")
            ]
            
            claim_lower = claim.lower()
            evidence_lower = evidence.lower()
            
            for positive, negative in contradictory_phrases:
                if positive in claim_lower and negative in evidence_lower:
                    return 0.8
                if negative in claim_lower and positive in evidence_lower:
                    return 0.8
            
            return 0.2
        except:
            return 0.2
    
    def _source_credibility_score(self, url, source):
        """Assign credibility boost based on source reliability"""
        high_credibility_domains = [
            "reuters.com", "apnews.com", "bbc.co.uk", "nytimes.com",
            "washingtonpost.com", "theguardian.com", "npr.org",
            "nasa.gov", "who.int", "un.org", "gov.uk", "gov.au"
        ]
        
        medium_credibility_domains = [
            "timesofindia.indiatimes.com", "thehindu.com", "cnn.com",
            "abcnews.go.com", "cbsnews.com", "nbcnews.com"
        ]
        
        url_lower = url.lower()
        
        for domain in high_credibility_domains:
            if domain in url_lower:
                return 0.15
        
        for domain in medium_credibility_domains:
            if domain in url_lower:
                return 0.08
        
        return 0.0

def decide_label_with_confidence(claim, evidence_evaluations):
    """Make final decision based on evidence evaluations"""
    if not evidence_evaluations:
        return "UNVERIFIED", 0.0, "No evidence found.", None
    
    # Sort by final score
    evidence_evaluations.sort(key=lambda x: x["final_score"], reverse=True)
    best_evidence = evidence_evaluations[0]
    
    score = best_evidence["final_score"]
    
    # Dynamic thresholds based on evidence quality
    if score >= 0.75:
        label = "VERIFIED"
        confidence = min(0.95, score)
    elif score >= 0.6:
        label = "LIKELY_TRUE"
        confidence = score
    elif score <= 0.3:
        label = "LIKELY_FALSE"
        confidence = 1 - score
    elif best_evidence["contradiction_detected"]:
        label = "CONTRADICTED"
        confidence = 0.8
    else:
        label = "UNVERIFIED"
        confidence = 0.5
    
    explanation = (
        f"Analysis based on {len(evidence_evaluations)} evidence sources. "
        f"Top evidence from {best_evidence['evidence_source']} shows "
        f"{score:.1%} confidence. Semantic similarity: {best_evidence['semantic_similarity']:.2f}, "
        f"Factual consistency: {best_evidence['factual_consistency']:.2f}"
    )
    
    return label, confidence, explanation, best_evidence