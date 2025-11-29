# #backend/agents/Source_credibility_keshav.py
# import os
# import re
# import json
# import requests
# from urllib.parse import quote
# import whois
# import tldextract
# from datetime import datetime, timezone
# import os
# from dotenv import load_dotenv
# from typing import Optional
# import logging
# from backend.agents.domain_age import calculate_domain_credibility
# # from domain_age import calculate_domain_credibility

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# ENV_PATH = os.path.join(BASE_DIR, ".env")
# load_dotenv(ENV_PATH)

# logger = logging.getLogger(__name__)


# # -------------------------------
# # Utility helpers
# # -------------------------------
# import tldextract

# def _domain_from_url_or_domain(url_or_domain: str, include_subdomain=True) -> str:
#     if "://" not in url_or_domain:
#         url_or_domain = "http://" + url_or_domain
#     ext = tldextract.extract(url_or_domain)
#     if not ext.domain or not ext.suffix:
#         return url_or_domain
#     if include_subdomain and ext.subdomain:
#         return f"{ext.subdomain}.{ext.domain}.{ext.suffix}"
#     else:
#         return f"{ext.domain}.{ext.suffix}"

# def _clamp(x, lo=0.0, hi=1.0):
#     return max(lo, min(hi, x))

# def _label(score):
#     if score >= 0.75:
#         return "High Credibility ✅"
#     elif score >= 0.5:
#         return "Moderate Credibility ⚖️"
#     else:
#         return "Low Credibility ⚠️"

# # -------------------------------
# # 1. NewsAPI check
# # -------------------------------
# def _newsapi_presence(domain: str):
#     try:
#         API_KEY = os.getenv("NEWSAPI_KEY")
#         resp = requests.get(
#             f"https://newsapi.org/v2/top-headlines/sources?apiKey={API_KEY}"
#         )
#         if resp.status_code != 200:
#             return {"ok": False, "error": resp.text}

#         sources = resp.json().get("sources", [])
#         present = any(domain in (s.get("url", "")) for s in sources)
#         return {"ok": True, "present": present}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# # -------------------------------
# # 2. GNews presence
# # -------------------------------
# def _gnews_presence(domain: str):
#     try:
#         API_KEY = os.getenv("GNEWS_API_KEY")
#         resp = requests.get(
#     f"https://gnews.io/api/v4/top-headlines?token={API_KEY}&lang=en&country=in&max=50"
# )
#         if resp.status_code != 200:
#             return {"ok": False, "error": resp.text}

#         articles = resp.json().get("articles", [])
#         # print(articles)
#         present = any(domain in (a.get("source", {}).get("url", "")) for a in articles)
#         return {"ok": True, "present": present}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# # -------------------------------
# # 3. NewsData.io presence
# # -------------------------------
# def _newsdata_presence(domain: str):
#     try:
#         API_KEY = os.getenv("NEWSDATA_API_KEY")
#         resp = requests.get(
#             f"https://newsdata.io/api/1/news?apikey={API_KEY}&q={domain}"
#         )
#         if resp.status_code != 200:
#             return {"ok": False, "error": resp.text}

#         results = resp.json().get("results", [])
#         present = any(domain in (r.get("link", "")) for r in results)
#         return {"ok": True, "present": present}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# def _google_fact_check_presence(query: str):
#     try:
#         API_KEY = os.getenv("GOOGLE_FC_API_KEY")
#         if not API_KEY:
#             return {"ok": False, "error": "GOOGLE_FC_API_KEY not set"}

#         all_claims = []
#         page_token = None
#         encoded_query = quote(query)

#         while True:
#             url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?key={API_KEY}&query={encoded_query}&pageSize=100"
#             if page_token:
#                 url += f"&pageToken={page_token}"

#             resp = requests.get(url)
#             if resp.status_code != 200:
#                 return {"ok": False, "error": resp.text}

#             data = resp.json()
#             claims = data.get("claims", [])
            
#             for c in claims:
#                 clean_claim = {
#                     "text": c.get("text"),
#                     "claimant": c.get("claimant"),
#                     "claimDate": c.get("claimDate"),
#                     "claimReview": [
#                         {
#                             "publisher": cr.get("publisher"),
#                             "url": cr.get("url"),
#                             "title": cr.get("title"),
#                             "reviewDate": cr.get("reviewDate"),
#                             "textualRating": cr.get("textualRating"),
#                             "languageCode": cr.get("languageCode"),
#                         } for cr in c.get("claimReview", [])
#                     ]
#                 }
#                 # print(clean_claim)
#                 # print("**********")
#                 all_claims.append(clean_claim)

#             page_token = data.get("nextPageToken")
#             if not page_token:
#                 break

#         return {"ok": True, "found": len(all_claims) > 0, "claims": all_claims}

#     except Exception as e:
#         return {"ok": False, "error": str(e)}
    
# def analyze_fact_check_credibility(fc_result):
#     """
#     Analyze fact check results to determine source credibility
#     CORRECTED VERSION: Properly handles true/false ratings
#     """
#     if not fc_result["ok"] or not fc_result["found"]:
#         return 0.0, "ℹ️ No fact-check data available"
    
#     claims = fc_result["claims"]
#     # print(claims[:10])
    
#     # Count claims actually MADE BY the source
#     claims_by_source = 0
#     true_claims = 0
#     false_claims = 0
#     mixed_claims = 0
#     unproven_claims = 0
    
#     # print(f"🔍 Analyzing fact-checks for {source_name}...")
    
#     for i, claim in enumerate(claims):
#         # claimant = claim.get("claimant", "").lower() if claim.get("claimant") else ""
        
#         # Only count claims where the source is actually the claimant
#         # if source_name.lower() in claimant:
#         # claims_by_source += 1
#         claim_text = claim.get("text", "")[:100] + "..."
#         print(f"  Claim {i+1} : {claim_text}")
            
#             # Analyze all English reviews for this claim
#         claim_rated = False
#         for review in claim.get("claimReview", []):
#                 rating = review.get("textualRating", "").lower()
#                 language = review.get("languageCode", "")
                
#                 if language == "en":  # Only English reviews
#                     print(f"    Rating: {rating}")
                    
#                     if any(word in rating for word in ["true", "correct", "accurate"]):
#                         true_claims += 1
#                         print(f"    → COUNTED AS: TRUE")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["false", "incorrect", "inaccurate","misleading"]):
#                         false_claims += 1
#                         print(f"    → COUNTED AS: FALSE")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["mostly true", "partly true", "half true"]):
#                         mixed_claims += 1
#                         print(f"    → COUNTED AS: MIXED")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["mostly false", "partly false"]):
#                         false_claims += 1  # Mostly false still counts as false
#                         print(f"    → COUNTED AS: FALSE (mostly false)")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["unproven", "cannot be determined"]):
#                         unproven_claims += 1
#                         print(f"    → COUNTED AS: UNPROVEN")
#                         claim_rated = True
#                         break
            
#         if not claim_rated:
#                 # If no English review or couldn't classify, count as unproven
#                 unproven_claims += 1
#                 print(f"    → COUNTED AS: UNPROVEN (no clear rating)")
    
#     print(f"\n📊 Fact-Check Summary for :")
#     print(f"  Total claims by source: {claims_by_source}")
#     print(f"  True claims: {true_claims}")
#     print(f"  False claims: {false_claims}") 
#     print(f"  Mixed claims: {mixed_claims}")
#     print(f"  Unproven claims: {unproven_claims}")
    
#     # Calculate credibility score based only on proven true/false claims
#     proven_claims = true_claims + false_claims + mixed_claims
    
#     if proven_claims > 0:
#         accuracy_ratio = true_claims / proven_claims
        
#         if accuracy_ratio >= 0.8:  # 80%+ accurate
#             score_adjustment = +0.15
#             reason = f"✅ High accuracy: {true_claims}/{proven_claims} proven claims true"
#         elif accuracy_ratio >= 0.6:  # 60-79% accurate
#             score_adjustment = +0.08
#             reason = f"⚠️ Moderate accuracy: {true_claims}/{proven_claims} proven claims true"
#         elif accuracy_ratio >= 0.4:  # 40-59% accurate
#             score_adjustment = 0.0
#             reason = f"ℹ️ Mixed accuracy: {true_claims}/{proven_claims} proven claims true"
#         elif accuracy_ratio >= 0.2:  # 20-39% accurate
#             score_adjustment = -0.10
#             reason = f"❌ Low accuracy: {true_claims}/{proven_claims} proven claims true"
#         else:  # <20% accurate
#             score_adjustment = -0.20
#             reason = f"🚨 Very low accuracy: {true_claims}/{proven_claims} proven claims true"
            
#     else:
#         # No proven claims (only unproven/mixed)
#         if claims_by_source > 0:
#             score_adjustment = 0.0
#             reason = f"ℹ️ No proven accuracy data ({claims_by_source} unproven claims)"
#         else:
#             # No claims actually BY the source
#             if len(claims) > 10:
#                 score_adjustment = +0.05
#                 reason = f"✅ Source rarely makes fact-checked claims ({len(claims)} total checks)"
#             else:
#                 score_adjustment = 0.0
#                 reason = f"ℹ️ Limited fact-check data ({len(claims)} total checks)"
    
#     return score_adjustment, reason

# def publication_reputation_check(url_or_domain: str):
#     domain = _domain_from_url_or_domain(url_or_domain)
#     print(f"\n🚀 Checking credibility for: {domain}")

#     score = 0.4  # Start with neutral score
#     reasons = []
#     signals = {}

#     # Extract publisher name from domain
#     ext = tldextract.extract(domain)
#     publisher_name = ext.domain.replace("-", " ").title()

#     # 1. GNews Presence (25% weight)
#     gnews = _gnews_presence(domain)
#     signals["gnews"] = gnews
#     if gnews["ok"]:
#         if gnews["present"]:
#             score += 0.20  # Increased from 0.1 to 0.25
#             reasons.append("✅ Ranked in Google News headlines")
#         else:
#             score -= 0.10  # Penalty for not being in GNews
#             reasons.append("❌ Not in Google News headlines")
#     else:
#         reasons.append("⚠️ GNews unavailable")

#     print("After GNews:", score)

#     # 2. NewsData.io Presence (25% weight)
#     newsdata = _newsdata_presence(domain)
#     signals["newsdata"] = newsdata
#     if newsdata["ok"]:
#         if newsdata["present"]:
#             score += 0.20  # Balanced with GNews
#             reasons.append("✅ Domain publishes on registered news data")
#         else:
#             score -= 0.10  # Penalty for not being in NewsData
#             reasons.append("❌ Domain not found in registered news data")
#     else:
#         reasons.append("⚠️ NewsData.io unavailable")

#     print("After NewsData:", score)

#     # 3. Domain Age (30% weight) - FIXED
#     # Get just the age score adjustment, not the full score
#     age_score_adjustment, age_reason, age_signals = calculate_domain_credibility(domain)
#     signals["domain_age"] = age_signals
#     score += age_score_adjustment  # This should be just the adjustment (-0.15 to +0.35)
#     reasons.append(age_reason)

#     print("After Domain Age:", score)

#     # 4. Fact Check (20% weight) - SIMPLIFIED
#     fc = _google_fact_check_presence(publisher_name)
#     signals["factcheck"] = fc
    
#     if fc["ok"]:
#         if fc["found"]:
#             # Use the new analysis function
#             fc_score_adjustment, fc_reason = analyze_fact_check_credibility(fc)
#             score = min(score + fc_score_adjustment, 1.0)
#             reasons.append(fc_reason)
#         else:
#             reasons.append("ℹ️ Not in Google Fact Check results")
#     else:
#         reasons.append("⚠️ Google Fact Check unavailable")

#     print("After Fact Check:", score)

#     # Final clamping
#     score = _clamp(score)
#     label = _label(score)
    
#     result = {
#         "domain": domain,
#         "score": round(score, 3),
#         "label": label,
#         "reasons": reasons,
#         "signals": signals,
#     }

#     print(f"\n📊 Final Score: {result['score']} → {result['label']}")
#     print(f"📌 Reasons: {reasons}")
#     return result

# if __name__ == "__main__":
#     # Example domains to test
#     test_domains = [
#         "https://www.indiatoday.in/india/story/karur-stampede-will-vijay-be-arrested-tamil-nadu-minister-durai-murugan-responds-2797752-2025-10-04"
#     ]

#     for d in test_domains:
#         result = publication_reputation_check(d)
#         print("\n--- Result ---")
#         # print(result)

# #backend/agents/Source_credibility_keshav.py
# import os
# import re
# import json
# import requests
# from urllib.parse import quote
# import whois
# import tldextract
# from datetime import datetime, timezone
# import os
# from dotenv import load_dotenv
# from typing import Optional
# import logging
# from domain_age import calculate_domain_credibility
# # from domain_age import calculate_domain_credibility

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# ENV_PATH = os.path.join(BASE_DIR, ".env")
# load_dotenv(ENV_PATH)

# logger = logging.getLogger(__name__)


# # -------------------------------
# # Utility helpers
# # -------------------------------
# import tldextract

# def _domain_from_url_or_domain(url_or_domain: str, include_subdomain=True) -> str:
#     if "://" not in url_or_domain:
#         url_or_domain = "http://" + url_or_domain
#     ext = tldextract.extract(url_or_domain)
#     if not ext.domain or not ext.suffix:
#         return url_or_domain
#     if include_subdomain and ext.subdomain:
#         return f"{ext.subdomain}.{ext.domain}.{ext.suffix}"
#     else:
#         return f"{ext.domain}.{ext.suffix}"

# def _clamp(x, lo=0.0, hi=1.0):
#     return max(lo, min(hi, x))

# def _label(score):
#     if score >= 0.75:
#         return "High Credibility ✅"
#     elif score >= 0.5:
#         return "Moderate Credibility ⚖️"
#     else:
#         return "Low Credibility ⚠️"

# # -------------------------------
# # 1. NewsAPI check
# # -------------------------------
# def _newsapi_presence(domain: str):
#     try:
#         API_KEY = os.getenv("NEWSAPI_KEY")
#         resp = requests.get(
#             f"https://newsapi.org/v2/top-headlines/sources?apiKey={API_KEY}"
#         )
#         if resp.status_code != 200:
#             return {"ok": False, "error": resp.text}

#         sources = resp.json().get("sources", [])
#         present = any(domain in (s.get("url", "")) for s in sources)
#         return {"ok": True, "present": present}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# # -------------------------------
# # 2. GNews presence
# # -------------------------------
# def _gnews_presence(domain: str):
#     try:
#         API_KEY = os.getenv("SERPER_API_KEY")
#         headers = {
#             'X-API-KEY': API_KEY,
#             'Content-Type': 'application/json'
#         }
        
#         data = {
#             "q": domain,
#             "num": 10,
#             "tbm": "nws"  # News search
#         }
        
#         resp = requests.post(
#             "https://google.serper.dev/search",
#             headers=headers,
#             json=data
#         )
        
#         if resp.status_code != 200:
#             return {"ok": False, "error": resp.text}

#         results = resp.json().get("news", [])
#         # Check if domain appears in any news results
#         present = any(domain in result.get("link", "") for result in results)
        
#         return {"ok": True, "present": present}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# # -------------------------------
# # 3. NewsData.io presence
# # -------------------------------
# def _newsdata_presence(domain: str):
#     try:
#         API_KEY = os.getenv("NEWSDATA_API_KEY")
#         # Clean the domain and use domain parameter instead of q
#         clean_domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
        
#         resp = requests.get(
#             f"https://newsdata.io/api/1/news?apikey={API_KEY}&domain={clean_domain}&size=5"
#         )
        
#         if resp.status_code != 200:
#             return {"ok": False, "error": resp.text}

#         results = resp.json().get("results", [])
#         present = len(results) > 0
#         return {"ok": True, "present": present, "articles_found": len(results)}
#     except Exception as e:
#         return {"ok": False, "error": str(e)}

# def _google_fact_check_presence(query: str):
#     try:
#         API_KEY = os.getenv("GOOGLE_FC_API_KEY")
#         if not API_KEY:
#             return {"ok": False, "error": "GOOGLE_FC_API_KEY not set"}

#         all_claims = []
#         page_token = None
#         encoded_query = quote(query)

#         while True:
#             url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?key={API_KEY}&query={encoded_query}&pageSize=100"
#             if page_token:
#                 url += f"&pageToken={page_token}"

#             resp = requests.get(url)
#             if resp.status_code != 200:
#                 return {"ok": False, "error": resp.text}

#             data = resp.json()
#             claims = data.get("claims", [])
            
#             for c in claims:
#                 clean_claim = {
#                     "text": c.get("text"),
#                     "claimant": c.get("claimant"),
#                     "claimDate": c.get("claimDate"),
#                     "claimReview": [
#                         {
#                             "publisher": cr.get("publisher"),
#                             "url": cr.get("url"),
#                             "title": cr.get("title"),
#                             "reviewDate": cr.get("reviewDate"),
#                             "textualRating": cr.get("textualRating"),
#                             "languageCode": cr.get("languageCode"),
#                         } for cr in c.get("claimReview", [])
#                     ]
#                 }
#                 # print(clean_claim)
#                 # print("**********")
#                 all_claims.append(clean_claim)

#             page_token = data.get("nextPageToken")
#             if not page_token:
#                 break

#         return {"ok": True, "found": len(all_claims) > 0, "claims": all_claims}

#     except Exception as e:
#         return {"ok": False, "error": str(e)}
    
# def analyze_fact_check_credibility(fc_result):
#     """
#     Analyze fact check results to determine source credibility
#     CORRECTED VERSION: Properly handles true/false ratings
#     """
#     if not fc_result["ok"] or not fc_result["found"]:
#         return 0.0, "ℹ️ No fact-check data available"
    
#     claims = fc_result["claims"]
#     # print(claims[:10])
    
#     # Count claims actually MADE BY the source
#     claims_by_source = 0
#     true_claims = 0
#     false_claims = 0
#     mixed_claims = 0
#     unproven_claims = 0
    
#     # print(f"🔍 Analyzing fact-checks for {source_name}...")
    
#     for i, claim in enumerate(claims):
#         # claimant = claim.get("claimant", "").lower() if claim.get("claimant") else ""
        
#         # Only count claims where the source is actually the claimant
#         # if source_name.lower() in claimant:
#         # claims_by_source += 1
#         claim_text = claim.get("text", "")[:100] + "..."
#         print(f"  Claim {i+1} : {claim_text}")
            
#             # Analyze all English reviews for this claim
#         claim_rated = False
#         for review in claim.get("claimReview", []):
#                 rating = review.get("textualRating", "").lower()
#                 language = review.get("languageCode", "")
                
#                 if language == "en":  # Only English reviews
#                     print(f"    Rating: {rating}")
                    
#                     if any(word in rating for word in ["true", "correct", "accurate"]):
#                         true_claims += 1
#                         print(f"    → COUNTED AS: TRUE")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["false", "incorrect", "inaccurate","misleading"]):
#                         false_claims += 1
#                         print(f"    → COUNTED AS: FALSE")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["mostly true", "partly true", "half true"]):
#                         mixed_claims += 1
#                         print(f"    → COUNTED AS: MIXED")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["mostly false", "partly false"]):
#                         false_claims += 1  # Mostly false still counts as false
#                         print(f"    → COUNTED AS: FALSE (mostly false)")
#                         claim_rated = True
#                         break
#                     elif any(word in rating for word in ["unproven", "cannot be determined"]):
#                         unproven_claims += 1
#                         print(f"    → COUNTED AS: UNPROVEN")
#                         claim_rated = True
#                         break
            
#         if not claim_rated:
#                 # If no English review or couldn't classify, count as unproven
#                 unproven_claims += 1
#                 print(f"    → COUNTED AS: UNPROVEN (no clear rating)")
    
#     print(f"\n📊 Fact-Check Summary for :")
#     print(f"  Total claims by source: {claims_by_source}")
#     print(f"  True claims: {true_claims}")
#     print(f"  False claims: {false_claims}") 
#     print(f"  Mixed claims: {mixed_claims}")
#     print(f"  Unproven claims: {unproven_claims}")
    
#     # Calculate credibility score based only on proven true/false claims
#     proven_claims = true_claims + false_claims + mixed_claims
    
#     if proven_claims > 0:
#         accuracy_ratio = true_claims / proven_claims
        
#         if accuracy_ratio >= 0.8:  # 80%+ accurate
#             score_adjustment = +0.15
#             reason = f"✅ High accuracy: {true_claims}/{proven_claims} proven claims true"
#         elif accuracy_ratio >= 0.6:  # 60-79% accurate
#             score_adjustment = +0.08
#             reason = f"⚠️ Moderate accuracy: {true_claims}/{proven_claims} proven claims true"
#         elif accuracy_ratio >= 0.4:  # 40-59% accurate
#             score_adjustment = 0.0
#             reason = f"ℹ️ Mixed accuracy: {true_claims}/{proven_claims} proven claims true"
#         elif accuracy_ratio >= 0.2:  # 20-39% accurate
#             score_adjustment = -0.10
#             reason = f"❌ Low accuracy: {true_claims}/{proven_claims} proven claims true"
#         else:  # <20% accurate
#             score_adjustment = -0.20
#             reason = f"🚨 Very low accuracy: {true_claims}/{proven_claims} proven claims true"
            
#     else:
#         # No proven claims (only unproven/mixed)
#         if claims_by_source > 0:
#             score_adjustment = 0.0
#             reason = f"ℹ️ No proven accuracy data ({claims_by_source} unproven claims)"
#         else:
#             # No claims actually BY the source
#             if len(claims) > 10:
#                 score_adjustment = +0.05
#                 reason = f"✅ Source rarely makes fact-checked claims ({len(claims)} total checks)"
#             else:
#                 score_adjustment = 0.0
#                 reason = f"ℹ️ Limited fact-check data ({len(claims)} total checks)"
    
#     return score_adjustment, reason

# def publication_reputation_check(url_or_domain: str):
#     domain = _domain_from_url_or_domain(url_or_domain)
#     print(f"\n🚀 Checking credibility for: {domain}")

#     score = 0.4  # Start with neutral score
#     reasons = []
#     signals = {}

#     # Extract publisher name from domain
#     ext = tldextract.extract(domain)
#     publisher_name = ext.domain.replace("-", " ").title()

#     # 1. GNews Presence (25% weight)
#     gnews = _gnews_presence(domain)
#     signals["gnews"] = gnews
#     if gnews["ok"]:
#         if gnews["present"]:
#             score += 0.20  # Increased from 0.1 to 0.25
#             reasons.append("✅ Ranked in Google News headlines")
#         else:
#             score -= 0.10  # Penalty for not being in GNews
#             reasons.append("❌ Not in Google News headlines")
#     else:
#         reasons.append("⚠️ GNews unavailable")

#     print("After GNews:", score)

#     # 2. NewsData.io Presence (25% weight)
#     newsdata = _newsdata_presence(domain)
#     signals["newsdata"] = newsdata
#     if newsdata["ok"]:
#         if newsdata["present"]:
#             score += 0.20  # Balanced with GNews
#             reasons.append("✅ Domain publishes on registered news data")
#         else:
#             score -= 0.10  # Penalty for not being in NewsData
#             reasons.append("❌ Domain not found in registered news data")
#     else:
#         reasons.append("⚠️ NewsData.io unavailable")

#     print("After NewsData:", score)

#     # 3. Domain Age (30% weight) - FIXED
#     # Get just the age score adjustment, not the full score
#     age_score_adjustment, age_reason, age_signals = calculate_domain_credibility(domain)
#     signals["domain_age"] = age_signals
#     score += age_score_adjustment  # This should be just the adjustment (-0.15 to +0.35)
#     reasons.append(age_reason)

#     print("After Domain Age:", score)

#     # 4. Fact Check (20% weight) - SIMPLIFIED
#     fc = _google_fact_check_presence(publisher_name)
#     signals["factcheck"] = fc
    
#     if fc["ok"]:
#         if fc["found"]:
#             # Use the new analysis function
#             fc_score_adjustment, fc_reason = analyze_fact_check_credibility(fc)
#             score = min(score + fc_score_adjustment, 1.0)
#             reasons.append(fc_reason)
#         else:
#             reasons.append("ℹ️ Not in Google Fact Check results")
#     else:
#         reasons.append("⚠️ Google Fact Check unavailable")

#     print("After Fact Check:", score)

#     # Final clamping
#     score = _clamp(score)
#     label = _label(score)
    
#     result = {
#         "domain": domain,
#         "score": round(score, 3),
#         "label": label,
#         "reasons": reasons,
#         "signals": signals,
#     }

#     print(f"\n📊 Final Score: {result['score']} → {result['label']}")
#     print(f"📌 Reasons: {reasons}")
#     return result

# if __name__ == "__main__":
#     # Example domains to test
#     test_domains = [
#         "https://www.indiatoday.in/india/story/karur-stampede-will-vijay-be-arrested-tamil-nadu-minister-durai-murugan-responds-2797752-2025-10-04"
#     ]

#     for d in test_domains:
#         result = publication_reputation_check(d)
#         print("\n--- Result ---")
#         # print(result)
# backend/agents/Source_credibility_keshav.py
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

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

logger = logging.getLogger(__name__)

# -------------------------------
# Utility helpers
# -------------------------------
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
# Source Classification
# -------------------------------
def _classify_source_type(domain: str):
    """
    Classify source type and provide base credibility score
    """
    domain_lower = domain.lower()
    
    # Major international news organizations
    major_news = [
        "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "cnn.com", 
        "nytimes.com", "theguardian.com", "wsj.com", "washingtonpost.com",
        "bloomberg.com", "forbes.com", "time.com", "newsweek.com"
    ]
    
    # Indian mainstream news
    indian_mainstream = [
        "indiatoday.in", "ndtv.com", "timesofindia.indiatimes.com", "thehindu.com",
        "hindustantimes.com", "indianexpress.com", "firstpost.com", "news18.com"
    ]
    
    # Regional/local news
    regional_news = [
        "deccanchronicle.com", "telegraphindia.com", "tribuneindia.com"
    ]
    
    # Low credibility indicators
    low_cred_indicators = [
        ".blog.", "medium.com", "blogspot.com", "wordpress.com", "weebly.com",
        "wixsite.com", ".blogspot.", "substack.com"
    ]
    
    # Check categories
    for source in major_news:
        if source in domain_lower:
            return "major_international_news", 0.7, "✅ Major international news organization"
    
    for source in indian_mainstream:
        if source in domain_lower:
            return "indian_mainstream_news", 0.65, "✅ Mainstream Indian news outlet"
    
    for source in regional_news:
        if source in domain_lower:
            return "regional_news", 0.5, "⚖️ Regional news outlet"
    
    for indicator in low_cred_indicators:
        if indicator in domain_lower:
            return "personal_blog", 0.2, "⚠️ Personal blog or platform"
    
    # Check for news-like domains
    if any(keyword in domain_lower for keyword in ["news", "times", "post", "tribune", "chronicle", "gazette"]):
        return "news_like_domain", 0.45, "ℹ️ News-like domain name"
    
    return "unknown", 0.4, "ℹ️ Standard website"

# -------------------------------
# 1. GNews presence
# -------------------------------
def _gnews_presence(domain: str):
    try:
        API_KEY = os.getenv("SERPER_API_KEY")
        if not API_KEY:
            return {"ok": False, "error": "SERPER_API_KEY not set"}
            
        headers = {
            'X-API-KEY': API_KEY,
            'Content-Type': 'application/json'
        }
        
        data = {
            "q": f"site:{domain}",
            "num": 10
        }
        
        resp = requests.post(
            "https://google.serper.dev/search",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if resp.status_code != 200:
            return {"ok": False, "error": resp.text}

        results = resp.json().get("organic", [])
        present = len(results) > 0
        return {"ok": True, "present": present, "results_count": len(results)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# -------------------------------
# 2. NewsData.io presence
# -------------------------------
def _newsdata_presence(domain: str):
    try:
        API_KEY = os.getenv("NEWSDATA_API_KEY")
        if not API_KEY:
            return {"ok": False, "error": "NEWSDATA_API_KEY not set"}
            
        # Clean the domain
        clean_domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
        
        resp = requests.get(
            f"https://newsdata.io/api/1/news?apikey={API_KEY}&domain={clean_domain}&size=10",
            timeout=10
        )
        
        if resp.status_code != 200:
            return {"ok": False, "error": resp.text}

        results = resp.json().get("results", [])
        present = len(results) > 0
        return {"ok": True, "present": present, "articles_found": len(results)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# -------------------------------
# 3. Google Fact Check
# -------------------------------
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

            resp = requests.get(url, timeout=10)
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
                all_claims.append(clean_claim)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return {"ok": True, "found": len(all_claims) > 0, "claims": all_claims}

    except Exception as e:
        return {"ok": False, "error": str(e)}

# -------------------------------
# Improved Fact Check Analysis
# -------------------------------
def analyze_fact_check_credibility(fc_result, source_domain: str):
    """
    Improved fact check analysis that properly attributes claims to sources
    """
    if not fc_result["ok"] or not fc_result["found"]:
        return 0.0, "ℹ️ No fact-check data available"
    
    claims = fc_result["claims"]
    if not claims:
        return 0.0, "ℹ️ No fact-check claims found"
    
    # Extract source name from domain for matching
    ext = tldextract.extract(source_domain)
    source_name_variants = [
        ext.domain,  # "indiatoday"
        ext.domain.replace("-", " "),  # "india today"
        f"{ext.domain}.{ext.suffix}"  # "indiatoday.in"
    ]
    
    source_claims = []
    
    # Filter claims by source
    for claim in claims:
        claimant = claim.get("claimant", "").lower() if claim.get("claimant") else ""
        claim_url = claim.get("url", "").lower() if claim.get("url") else ""
        
        # Check if this claim is from our source
        is_from_source = False
        
        # Check claimant name
        for variant in source_name_variants:
            if variant and variant.lower() in claimant:
                is_from_source = True
                break
        
        # Check URL
        if not is_from_source and source_domain.lower() in claim_url:
            is_from_source = True
        
        if is_from_source:
            source_claims.append(claim)
    
    print(f"🔍 Found {len(source_claims)} claims attributed to {source_domain}")
    
    if not source_claims:
        # If no direct claims, check if domain appears in any claims at all
        domain_mentioned = any(
            source_domain.lower() in str(claim.get("text", "")).lower() or 
            source_domain.lower() in str(claim.get("url", "")).lower() 
            for claim in claims
        )
        
        if domain_mentioned:
            return 0.0, "ℹ️ Domain mentioned in fact-checks but not as claimant"
        else:
            return 0.0, "ℹ️ No fact-checks directly related to this domain"
    
    # Analyze the source's claims
    true_claims = 0
    false_claims = 0
    mixed_claims = 0
    unrated_claims = 0
    
    for claim in source_claims:
        claim_rated = False
        
        for review in claim.get("claimReview", []):
            rating = review.get("textualRating", "").lower()
            language = review.get("languageCode", "")
            
            if language == "en":  # Only English reviews
                if any(word in rating for word in ["true", "correct", "accurate"]):
                    true_claims += 1
                    claim_rated = True
                    break
                elif any(word in rating for word in ["false", "incorrect", "inaccurate", "misleading"]):
                    false_claims += 1
                    claim_rated = True
                    break
                elif any(word in rating for word in ["mostly true", "partly true", "half true"]):
                    mixed_claims += 1
                    claim_rated = True
                    break
                elif any(word in rating for word in ["mostly false", "partly false"]):
                    false_claims += 1
                    claim_rated = True
                    break
                elif any(word in rating for word in ["unproven", "cannot be determined"]):
                    unrated_claims += 1
                    claim_rated = True
                    break
        
        if not claim_rated:
            unrated_claims += 1
    
    print(f"📊 Fact-check breakdown: {true_claims} true, {false_claims} false, {mixed_claims} mixed, {unrated_claims} unrated")
    
    # Calculate credibility adjustment
    total_rated = true_claims + false_claims + mixed_claims
    
    if total_rated > 0:
        accuracy_ratio = (true_claims + mixed_claims * 0.5) / total_rated
        
        if accuracy_ratio >= 0.8:
            adjustment = +0.15
            reason = f"✅ Excellent fact-check record: {true_claims}/{total_rated} claims rated true"
        elif accuracy_ratio >= 0.6:
            adjustment = +0.08
            reason = f"✅ Good fact-check record: {true_claims}/{total_rated} claims rated true"
        elif accuracy_ratio >= 0.4:
            adjustment = 0.0
            reason = f"⚖️ Mixed fact-check record: {true_claims}/{total_rated} claims rated true"
        elif accuracy_ratio >= 0.2:
            adjustment = -0.10
            reason = f"⚠️ Poor fact-check record: {true_claims}/{total_rated} claims rated true"
        else:
            adjustment = -0.20
            reason = f"❌ Very poor fact-check record: {true_claims}/{total_rated} claims rated true"
    else:
        # No rated claims
        if len(source_claims) > 0:
            adjustment = 0.0
            reason = f"ℹ️ {len(source_claims)} claims found but none rated"
        else:
            adjustment = 0.0
            reason = "ℹ️ No fact-check data available for this source"
    
    return adjustment, reason

# -------------------------------
# Main Credibility Check Function
# -------------------------------
def publication_reputation_check(url_or_domain: str):
    domain = _domain_from_url_or_domain(url_or_domain)
    print(f"\n🚀 Checking credibility for: {domain}")

    # Start with classification-based score
    source_type, base_score, type_reason = _classify_source_type(domain)
    score = base_score
    reasons = [type_reason]
    signals = {
        "source_type": source_type,
        "base_score": base_score
    }

    print(f"📊 Starting score ({source_type}): {score}")

    # 1. GNews Presence (20% weight)
    gnews = _gnews_presence(domain)
    signals["gnews"] = gnews
    if gnews["ok"]:
        if gnews["present"]:
            score += 0.15
            reasons.append(f"✅ Featured in Google News ({gnews.get('results_count', 0)} results)")
        else:
            # Only penalize if it's supposed to be a news source
            if "news" in source_type:
                score -= 0.05
                reasons.append("❌ Not found in Google News")
            else:
                reasons.append("ℹ️ Not in Google News (expected for non-news sites)")
    else:
        reasons.append("⚠️ GNews check unavailable")

    print(f"After GNews: {score}")

    # 2. NewsData.io Presence (20% weight)
    newsdata = _newsdata_presence(domain)
    signals["newsdata"] = newsdata
    if newsdata["ok"]:
        if newsdata["present"]:
            score += 0.15
            reasons.append(f"✅ Registered news source ({newsdata.get('articles_found', 0)} articles)")
        else:
            if "news" in source_type:
                score -= 0.05
                reasons.append("❌ Not in news database")
            else:
                reasons.append("ℹ️ Not in news database (expected)")
    else:
        reasons.append("⚠️ NewsData.io check unavailable")

    print(f"After NewsData: {score}")

    # 3. Domain Age (25% weight)
    age_adjustment, age_reason, age_signals = calculate_domain_credibility(domain)
    signals["domain_age"] = age_signals
    score += age_adjustment
    reasons.append(age_reason)

    print(f"After Domain Age: {score}")

    # 4. Fact Check (15% weight) - Use domain for better matching
    ext = tldextract.extract(domain)
    publisher_name = ext.domain.replace("-", " ").title()
    fc = _google_fact_check_presence(publisher_name)
    signals["factcheck"] = fc
    
    if fc["ok"]:
        fc_adjustment, fc_reason = analyze_fact_check_credibility(fc, domain)
        score += fc_adjustment
        reasons.append(fc_reason)
    else:
        reasons.append("⚠️ Fact Check unavailable")

    print(f"After Fact Check: {score}")

    # 5. Additional bonus for established news sources
    if "news" in source_type and score < 0.7:
        # Boost established news sources that passed basic checks
        news_bonus = 0.1
        score += news_bonus
        reasons.append("📰 Bonus: Established news organization")

    print(f"After News Bonus: {score}")

    # Final clamping and rounding
    score = _clamp(score)
    final_score = round(score, 3)
    label = _label(final_score)
    
    result = {
        "domain": domain,
        "source_type": source_type,
        "score": final_score,
        "label": label,
        "reasons": reasons,
        "signals": signals,
    }

    print(f"\n🎯 Final Score: {result['score']} → {result['label']}")
    print("📌 Reasons:")
    for reason in reasons:
        print(f"   - {reason}")
    
    return result

# -------------------------------
# Test Function
# -------------------------------
def test_credibility_checker():
    """Test the credibility checker with various domains"""
    test_domains = [
        "https://www.indiatoday.in/india/story/karur-stampede-will-vijay-be-arrested-tamil-nadu-minister-durai-murugan-responds-2797752-2025-10-04",
        "reuters.com",
        "bbc.com", 
        "cnn.com",
        "nytimes.com",
        "medium.com",
        "some-random-blog.blogspot.com"
    ]

    print("🧪 Testing Source Credibility Checker\n")
    
    for domain in test_domains:
        print("=" * 60)
        result = publication_reputation_check(domain)
        print(f"Domain: {result['domain']}")
        print(f"Type: {result['source_type']}")
        print(f"Score: {result['score']} → {result['label']}")
        print()

if __name__ == "__main__":
    test_credibility_checker()