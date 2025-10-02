
import requests
from urllib.parse import quote
import whois
import tldextract
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
load_dotenv()

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

# -------------------------------
# 4. WHOIS age
# -------------------------------

def get_domain_age_days(domain: str):
    """
    Try WHOIS first, fallback to Wayback Machine.
    Returns domain age in days (int) or None if unavailable.
    """
    # --- WHOIS method ---
    try:
        w = whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list):
            created = created[0]
        if created:
            return (datetime.now() - created).days
    except Exception:
        pass  # WHOIS may fail (esp. for .in, .uk)

    # --- Wayback Machine fallback ---
    try:
        url = f"http://archive.org/wayback/available?url={domain}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            archived = data.get("archived_snapshots", {}).get("closest")
            if archived:
                timestamp = archived.get("timestamp")
                if timestamp:
                    snap_date = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
                    return (datetime.now() - snap_date).days
    except Exception:
        pass

    return None

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
                all_claims.append(clean_claim)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return {"ok": True, "found": len(all_claims) > 0, "claims": all_claims}

    except Exception as e:
        return {"ok": False, "error": str(e)}
# -------------------------------
# MAIN FUNCTION
# -------------------------------
# def publication_reputation_check(url_or_domain: str):
#     domain = _domain_from_url_or_domain(url_or_domain)
#     print(f"\n🚀 Checking credibility for: {domain}")

#     score = 0.5
#     reasons = []
#     signals = {}

#     # # NewsAPI
#     # newsapi = _newsapi_presence(domain)
#     # signals["newsapi"] = newsapi
#     # if newsapi["ok"]:
#     #     if newsapi["present"]:
#     #         score += 0.2
#     #         reasons.append("In NewsAPI source list")
#     #     else:
#     #         reasons.append("Not in NewsAPI sources")
#     # else:
#     #     reasons.append("NewsAPI unavailable")

#     # GNews
#     gnews = _gnews_presence(domain)
#     signals["gnews"] = gnews
#     if gnews["ok"]:
#         if gnews["present"]:
#             score += 0.1
#             reasons.append("Ranked in GNews headlines")
#         else:
#             reasons.append("Not in GNews headlines")
#     else:
#         reasons.append("GNews unavailable")

#     # NewsData.io
#     newsdata = _newsdata_presence(domain)
#     signals["newsdata"] = newsdata
#     if newsdata["ok"]:
#         if newsdata["present"]:
#             score += 0.2
#             reasons.append("Domain publishes on NewsData.io")
#         else:
#             reasons.append("Domain not found in NewsData.io")
#     else:
#         reasons.append("NewsData.io unavailable")

#     # WHOIS
#     age_days = get_domain_age_days(domain)
#     signals["domain_age_days"] = age_days
#     if age_days is not None:
#         if age_days > 3650:
#             score += 0.05
#             reasons.append("Domain >10 years old (WHOIS)")
#         elif age_days < 365:
#             score -= 0.1
#             reasons.append("Domain <1 year old (WHOIS)")
#         else:
#             reasons.append("Domain age neutral (WHOIS)")
#     else:
#         reasons.append("WHOIS lookup failed")

#     # Wayback
#     # wb = _wayback_first_snapshot(domain)
#     # signals["wayback"] = wb
#     # if wb["ok"] and wb["age_days"] is not None:
#     #     if wb["age_days"] > 3650:
#     #         score += 0.1
#     #         reasons.append("Domain >10 years old (Wayback)")
#     #     elif wb["age_days"] < 365:
#     #         score -= 0.1
#     #         reasons.append("Domain <1 year old (Wayback)")
#     #     else:
#     #         reasons.append("Domain age neutral (Wayback)")
#     # else:
#     #     reasons.append("Wayback data unavailable")


#     # Fact check
#     fc = _google_fact_check_presence(domain)
#     signals["factcheck"] = fc
#     if fc["ok"]:
#         if fc["found"]:
#             claims = fc.get("claims", [])
#             total = len(claims)
#             false_misleading = sum(
#                 1 for c in claims
#                 if any(r.get("textualRating", "").lower() in ["false", "misleading", "altered photo"]
#                        for r in c.get("claimReview", []))
#             )
#             true_claims = total - false_misleading
#             if total > 0:
#                 credibility_ratio = true_claims / total
#                 score += (credibility_ratio - 0.5) * 0.6
#                 reasons.append(f"Fact-checked claims: {total}, credibility ratio: {credibility_ratio:.2f}")
#         else:
#             reasons.append("Not in Google Fact Check results")
#     else:
#         reasons.append("Google Fact Check unavailable")

#     # Finalize
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

def publication_reputation_check(url_or_domain: str):
    domain = _domain_from_url_or_domain(url_or_domain)
    print(f"\n🚀 Checking credibility for: {domain}")

    score = 0.5
    reasons = []
    signals = {}

    # Extract publisher name from domain
    ext = tldextract.extract(domain)
    publisher_name = ext.domain.replace("-", " ").title()  # e.g. 'aljazeera' -> 'Aljazeera'

    # GNews
    gnews = _gnews_presence(domain)
    signals["gnews"] = gnews
    if gnews["ok"]:
        if gnews["present"]:
            score += 0.1
            reasons.append("Ranked in GNews headlines")
        else:
            reasons.append("Not in GNews headlines")
    else:
        reasons.append("GNews unavailable")

    # NewsData.io
    newsdata = _newsdata_presence(domain)
    signals["newsdata"] = newsdata
    if newsdata["ok"]:
        if newsdata["present"]:
            score += 0.2
            reasons.append("Domain publishes on NewsData.io")
        else:
            reasons.append("Domain not found in NewsData.io")
    else:
        reasons.append("NewsData.io unavailable")

    # WHOIS age
    age_days = get_domain_age_days(domain)
    signals["domain_age_days"] = age_days
    if age_days is not None:
        if age_days > 3650:
            score += 0.05
            reasons.append("Domain >10 years old (WHOIS)")
        elif age_days < 365:
            score -= 0.1
            reasons.append("Domain <1 year old (WHOIS)")
        else:
            reasons.append("Domain age neutral (WHOIS)")
    else:
        reasons.append("WHOIS lookup failed")

    # Fact check
    fc = _google_fact_check_presence(publisher_name)  # Use publisher name here!
    signals["factcheck"] = fc
    if fc["ok"]:
        if fc["found"]:
            claims = fc.get("claims", [])
            total = len(claims)
            false_misleading = sum(
                1 for c in claims
                if any(r.get("textualRating", "").lower() in ["false", "misleading", "altered photo"]
                       for r in c.get("claimReview", []))
            )
            true_claims = total - false_misleading
            if total > 0:
                credibility_ratio = true_claims / total
                score += (credibility_ratio - 0.5) * 0.6
                reasons.append(f"Fact-checked claims: {total}, credibility ratio: {credibility_ratio:.2f}")
        else:
            reasons.append("Not in Google Fact Check results")
    else:
        reasons.append("Google Fact Check unavailable")

    # Finalize
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
        "https://www.aljazeera.com/news/2025/9/6/after-trump-jab-indias-modi-says-ties-with-us-still-very-positive"
    ]

    for d in test_domains:
        result = publication_reputation_check(d)
        print("\n--- Result ---")
        print(result)