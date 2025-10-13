#backend/agents/Source_credibility_keshav.py
import os
import re
import json
import requests
from urllib.parse import quote
import whois
import tldextract
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from typing import Optional
import logging
from backend.agents.domain_age import calculate_domain_credibility
# from domain_age import calculate_domain_credibility

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

logger = logging.getLogger(__name__)


# -------------------------------
# Utility helpers
# -------------------------------
import tldextract

def _domain_from_url_or_domain(url_or_domain: str, include_subdomain=True) -> str:
    if "://" not in url_or_domain:
        url_or_domain = "http://" + url_or_domain
    ext = tldextract.extract(url_or_domain)
    if not ext.domain or not ext.suffix:
        return url_or_domain
    if include_subdomain and ext.subdomain:
        return f"{ext.subdomain}.{ext.domain}.{ext.suffix}"
    else:
        return f"{ext.domain}.{ext.suffix}"

def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def _label(score):
    if score >= 0.75:
        return "High Credibility ✅"
    elif score >= 0.5:
        return "Moderate Credibility ⚖️"
    else:
        return "Low Credibility ⚠️"

# -------------------------------
# 1. NewsAPI check
# -------------------------------
def _newsapi_presence(domain: str):
    try:
        API_KEY = os.getenv("NEWSAPI_KEY")
        resp = requests.get(
            f"https://newsapi.org/v2/top-headlines/sources?apiKey={API_KEY}"
        )
        if resp.status_code != 200:
            return {"ok": False, "error": resp.text}

        sources = resp.json().get("sources", [])
        present = any(domain in (s.get("url", "")) for s in sources)
        return {"ok": True, "present": present}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# -------------------------------
# 2. GNews presence
# -------------------------------
def _gnews_presence(domain: str):
    try:
        API_KEY = os.getenv("GNEWS_API_KEY")
        resp = requests.get(
    f"https://gnews.io/api/v4/top-headlines?token={API_KEY}&lang=en&country=in&max=50"
)
        if resp.status_code != 200:
            return {"ok": False, "error": resp.text}

        articles = resp.json().get("articles", [])
        # print(articles)
        present = any(domain in (a.get("source", {}).get("url", "")) for a in articles)
        return {"ok": True, "present": present}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# -------------------------------
# 3. NewsData.io presence
# -------------------------------
def _newsdata_presence(domain: str):
    try:
        API_KEY = os.getenv("NEWSDATA_API_KEY")
        resp = requests.get(
            f"https://newsdata.io/api/1/news?apikey={API_KEY}&q={domain}"
        )
        if resp.status_code != 200:
            return {"ok": False, "error": resp.text}

        results = resp.json().get("results", [])
        present = any(domain in (r.get("link", "")) for r in results)
        return {"ok": True, "present": present}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _google_fact_check_presence(query: str):
    try:
        API_KEY = os.getenv("GOOGLE_FC_API_KEY")
        if not API_KEY:
            return {"ok": False, "error": "GOOGLE_FC_API_KEY not set"}

        all_claims = []
        page_token = None
        encoded_query = quote(query)

        while True:
            url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?key={API_KEY}&query={encoded_query}&pageSize=100"
            if page_token:
                url += f"&pageToken={page_token}"

            resp = requests.get(url)
            if resp.status_code != 200:
                return {"ok": False, "error": resp.text}

            data = resp.json()
            claims = data.get("claims", [])
            
            for c in claims:
                clean_claim = {
                    "text": c.get("text"),
                    "claimant": c.get("claimant"),
                    "claimDate": c.get("claimDate"),
                    "claimReview": [
                        {
                            "publisher": cr.get("publisher"),
                            "url": cr.get("url"),
                            "title": cr.get("title"),
                            "reviewDate": cr.get("reviewDate"),
                            "textualRating": cr.get("textualRating"),
                            "languageCode": cr.get("languageCode"),
                        } for cr in c.get("claimReview", [])
                    ]
                }
                # print(clean_claim)
                # print("**********")
                all_claims.append(clean_claim)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return {"ok": True, "found": len(all_claims) > 0, "claims": all_claims}

    except Exception as e:
        return {"ok": False, "error": str(e)}
    
def analyze_fact_check_credibility(fc_result):
    """
    Analyze fact check results to determine source credibility
    CORRECTED VERSION: Properly handles true/false ratings
    """
    if not fc_result["ok"] or not fc_result["found"]:
        return 0.0, "ℹ️ No fact-check data available"
    
    claims = fc_result["claims"]
    # print(claims[:10])
    
    # Count claims actually MADE BY the source
    claims_by_source = 0
    true_claims = 0
    false_claims = 0
    mixed_claims = 0
    unproven_claims = 0
    
    # print(f"🔍 Analyzing fact-checks for {source_name}...")
    
    for i, claim in enumerate(claims):
        # claimant = claim.get("claimant", "").lower() if claim.get("claimant") else ""
        
        # Only count claims where the source is actually the claimant
        # if source_name.lower() in claimant:
        # claims_by_source += 1
        claim_text = claim.get("text", "")[:100] + "..."
        print(f"  Claim {i+1} : {claim_text}")
            
            # Analyze all English reviews for this claim
        claim_rated = False
        for review in claim.get("claimReview", []):
                rating = review.get("textualRating", "").lower()
                language = review.get("languageCode", "")
                
                if language == "en":  # Only English reviews
                    print(f"    Rating: {rating}")
                    
                    if any(word in rating for word in ["true", "correct", "accurate"]):
                        true_claims += 1
                        print(f"    → COUNTED AS: TRUE")
                        claim_rated = True
                        break
                    elif any(word in rating for word in ["false", "incorrect", "inaccurate","misleading"]):
                        false_claims += 1
                        print(f"    → COUNTED AS: FALSE")
                        claim_rated = True
                        break
                    elif any(word in rating for word in ["mostly true", "partly true", "half true"]):
                        mixed_claims += 1
                        print(f"    → COUNTED AS: MIXED")
                        claim_rated = True
                        break
                    elif any(word in rating for word in ["mostly false", "partly false"]):
                        false_claims += 1  # Mostly false still counts as false
                        print(f"    → COUNTED AS: FALSE (mostly false)")
                        claim_rated = True
                        break
                    elif any(word in rating for word in ["unproven", "cannot be determined"]):
                        unproven_claims += 1
                        print(f"    → COUNTED AS: UNPROVEN")
                        claim_rated = True
                        break
            
        if not claim_rated:
                # If no English review or couldn't classify, count as unproven
                unproven_claims += 1
                print(f"    → COUNTED AS: UNPROVEN (no clear rating)")
    
    print(f"\n📊 Fact-Check Summary for :")
    print(f"  Total claims by source: {claims_by_source}")
    print(f"  True claims: {true_claims}")
    print(f"  False claims: {false_claims}") 
    print(f"  Mixed claims: {mixed_claims}")
    print(f"  Unproven claims: {unproven_claims}")
    
    # Calculate credibility score based only on proven true/false claims
    proven_claims = true_claims + false_claims + mixed_claims
    
    if proven_claims > 0:
        accuracy_ratio = true_claims / proven_claims
        
        if accuracy_ratio >= 0.8:  # 80%+ accurate
            score_adjustment = +0.15
            reason = f"✅ High accuracy: {true_claims}/{proven_claims} proven claims true"
        elif accuracy_ratio >= 0.6:  # 60-79% accurate
            score_adjustment = +0.08
            reason = f"⚠️ Moderate accuracy: {true_claims}/{proven_claims} proven claims true"
        elif accuracy_ratio >= 0.4:  # 40-59% accurate
            score_adjustment = 0.0
            reason = f"ℹ️ Mixed accuracy: {true_claims}/{proven_claims} proven claims true"
        elif accuracy_ratio >= 0.2:  # 20-39% accurate
            score_adjustment = -0.10
            reason = f"❌ Low accuracy: {true_claims}/{proven_claims} proven claims true"
        else:  # <20% accurate
            score_adjustment = -0.20
            reason = f"🚨 Very low accuracy: {true_claims}/{proven_claims} proven claims true"
            
    else:
        # No proven claims (only unproven/mixed)
        if claims_by_source > 0:
            score_adjustment = 0.0
            reason = f"ℹ️ No proven accuracy data ({claims_by_source} unproven claims)"
        else:
            # No claims actually BY the source
            if len(claims) > 10:
                score_adjustment = +0.05
                reason = f"✅ Source rarely makes fact-checked claims ({len(claims)} total checks)"
            else:
                score_adjustment = 0.0
                reason = f"ℹ️ Limited fact-check data ({len(claims)} total checks)"
    
    return score_adjustment, reason

def publication_reputation_check(url_or_domain: str):
    domain = _domain_from_url_or_domain(url_or_domain)
    print(f"\n🚀 Checking credibility for: {domain}")

    score = 0.4  # Start with neutral score
    reasons = []
    signals = {}

    # Extract publisher name from domain
    ext = tldextract.extract(domain)
    publisher_name = ext.domain.replace("-", " ").title()

    # 1. GNews Presence (25% weight)
    gnews = _gnews_presence(domain)
    signals["gnews"] = gnews
    if gnews["ok"]:
        if gnews["present"]:
            score += 0.20  # Increased from 0.1 to 0.25
            reasons.append("✅ Ranked in Google News headlines")
        else:
            score -= 0.10  # Penalty for not being in GNews
            reasons.append("❌ Not in Google News headlines")
    else:
        reasons.append("⚠️ GNews unavailable")

    print("After GNews:", score)

    # 2. NewsData.io Presence (25% weight)
    newsdata = _newsdata_presence(domain)
    signals["newsdata"] = newsdata
    if newsdata["ok"]:
        if newsdata["present"]:
            score += 0.20  # Balanced with GNews
            reasons.append("✅ Domain publishes on registered news data")
        else:
            score -= 0.10  # Penalty for not being in NewsData
            reasons.append("❌ Domain not found in registered news data")
    else:
        reasons.append("⚠️ NewsData.io unavailable")

    print("After NewsData:", score)

    # 3. Domain Age (30% weight) - FIXED
    # Get just the age score adjustment, not the full score
    age_score_adjustment, age_reason, age_signals = calculate_domain_credibility(domain)
    signals["domain_age"] = age_signals
    score += age_score_adjustment  # This should be just the adjustment (-0.15 to +0.35)
    reasons.append(age_reason)

    print("After Domain Age:", score)

    # 4. Fact Check (20% weight) - SIMPLIFIED
    fc = _google_fact_check_presence(publisher_name)
    signals["factcheck"] = fc
    
    if fc["ok"]:
        if fc["found"]:
            # Use the new analysis function
            fc_score_adjustment, fc_reason = analyze_fact_check_credibility(fc)
            score = min(score + fc_score_adjustment, 1.0)
            reasons.append(fc_reason)
        else:
            reasons.append("ℹ️ Not in Google Fact Check results")
    else:
        reasons.append("⚠️ Google Fact Check unavailable")

    print("After Fact Check:", score)

    # Final clamping
    score = _clamp(score)
    label = _label(score)
    
    result = {
        "domain": domain,
        "score": round(score, 3),
        "label": label,
        "reasons": reasons,
        "signals": signals,
    }

    print(f"\n📊 Final Score: {result['score']} → {result['label']}")
    print(f"📌 Reasons: {reasons}")
    return result

if __name__ == "__main__":
    # Example domains to test
    test_domains = [
        "https://www.indiatoday.in/india/story/karur-stampede-will-vijay-be-arrested-tamil-nadu-minister-durai-murugan-responds-2797752-2025-10-04"
    ]

    for d in test_domains:
        result = publication_reputation_check(d)
        print("\n--- Result ---")
        # print(result)