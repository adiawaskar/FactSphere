import os
import re
import json
import requests
import tldextract
import whois
from urllib.parse import urlparse
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()  # loads environment variables from .env file

# Utility helpers
def _domain_from_url_or_domain(value: str) -> str:
    if not re.search(r"://", value):
        netloc = value.strip().lower()
    else:
        netloc = urlparse(value).netloc.lower() or ""
    ext = tldextract.extract(netloc)
    return f"{ext.domain}.{ext.suffix}" if ext.suffix else netloc

def _clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))

def _label(score: float) -> str:
    return "High" if score >= 0.75 else "Medium" if score >= 0.5 else "Low"

def _get_domain_age_days(domain: str):
    print(f"🔎 Checking WHOIS info for domain: {domain}")
    try:
        w = whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list): created = created[0]
        if isinstance(created, datetime):
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - created).days
            print(f"✅ Domain age: {age} days")
            return age
    except Exception as e:
        print(f"⚠️ WHOIS lookup failed: {e}")
        return None
    return None

# Free external signals

def _newsapi_presence(domain: str):
    print(f"\n📰 Checking NewsAPI sources for: {domain}")
    api_key = os.getenv("NEWSAPI_KEY")
    ret = {"ok": False, "present": False, "raw": None, "error": None}
    if not api_key:
        print("⚠️ NEWSAPI_KEY not set.")
        ret["error"] = "NEWSAPI_KEY not set"
        return ret
    try:
        url = f"https://newsapi.org/v2/sources?language=en&apiKey={api_key}"
        r = requests.get(url, timeout=10)
        print(f"🔎 NewsAPI response: {r.status_code}")
        # print(json.dumps(r.json(), indent=2)) 
        if r.status_code == 200:
            sources = r.json().get("sources", [])
            for s in sources:
                d = _domain_from_url_or_domain(s.get("url", ""))
                if d == domain:
                    print(f"✅ Found {domain} in NewsAPI sources list")
                    ret.update({"ok": True, "present": True})
                    return ret
            print(f"❌ {domain} not in NewsAPI sources list")
            ret["ok"] = True
        else:
            print(f"⚠️ NewsAPI error: {r.text[:200]}")
            ret["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        print(f"⚠️ NewsAPI failed: {e}")
        ret["error"] = str(e)
    return ret

def _gnews_presence(domain: str):
    print(f"\n📰 Checking GNews headlines for: {domain}")
    api_key = os.getenv("GNEWS_API_KEY")
    ret = {"ok": False, "present": False, "raw": None, "error": None}
    if not api_key:
        print("⚠️ GNEWS_API_KEY not set.")
        ret["error"] = "GNEWS_API_KEY not set"
        return ret
    try:
        url = f"https://gnews.io/api/v4/top-headlines?lang=en&token={api_key}&max=50"
        r = requests.get(url, timeout=10)
        print(f"🔎 GNews response: {r.status_code}")
        # print(json.dumps(r.json(), indent=2)) 
        if r.status_code == 200:
            for art in r.json().get("articles", []):
                if _domain_from_url_or_domain(art.get("url", "")) == domain:
                    print(f"✅ Found {domain} in GNews top headlines")
                    ret.update({"ok": True, "present": True})
                    return ret
            print(f"❌ {domain} not in GNews top headlines")
            ret["ok"] = True
        else:
            print(f"⚠️ GNews error: {r.text[:200]}")
            ret["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        print(f"⚠️ GNews failed: {e}")
        ret["error"] = str(e)
    return ret

# def _google_fact_check_presence(domain: str):
#     print(f"\n🔎 Checking Google Fact Check API for: {domain}")
#     api_key = os.getenv("GOOGLE_FC_API_KEY")
#     ret = {"ok": False, "found": False, "raw": None, "error": None}
#     if not api_key:
#         print("⚠️ GOOGLE_FC_API_KEY not set.")
#         ret["error"] = "GOOGLE_FC_API_KEY not set"
#         return ret
#     try:
#         url = ("https://factchecktools.googleapis.com/v1alpha1/claims:search?key="
#                f"{api_key}&languageCode=en&query={domain}")
#         r = requests.get(url, timeout=10)
#         print(f"🔎 Google Fact Check response: {r.status_code}")
#         # print(json.dumps(r.json(), indent=2))
#         if r.status_code == 200 and r.json().get("claims"):
#             print(f"⚠️ {domain} has fact-check claims (possible controversy)")
#             ret.update({"ok": True, "found": True, "claims": r.json().get("claims")})
#         else:
#             print(f"✅ {domain} has no flagged claims in Fact Check API")
#             ret["ok"] = True
#         return ret
#     except Exception as e:
#         print(f"⚠️ Google Fact Check failed: {e}")
#         ret["error"] = str(e)
#     return ret
def _google_fact_check_presence(domain: str):
    print(f"\n🔎 Checking Google Fact Check API for: {domain}")
    api_key = os.getenv("GOOGLE_FC_API_KEY")
    ret = {"ok": False, "found": False, "raw": None, "error": None, "claims": []}
    if not api_key:
        print("⚠️ GOOGLE_FC_API_KEY not set.")
        ret["error"] = "GOOGLE_FC_API_KEY not set"
        return ret

    all_claims = []
    next_token = None

    try:
        while True:
            url = ("https://factchecktools.googleapis.com/v1alpha1/claims:search?"
                   f"key={api_key}&languageCode=en&query={domain}")
            if next_token:
                url += f"&pageToken={next_token}"

            r = requests.get(url, timeout=10)
            data = r.json()
            if r.status_code != 200:
                print(f"⚠️ Google Fact Check API error: {r.text[:200]}")
                ret["error"] = f"HTTP {r.status_code}"
                break

            claims_page = data.get("claims", [])
            all_claims.extend(claims_page)
            next_token = data.get("nextPageToken")
            if not next_token:
                break

        ret["ok"] = True
        if all_claims:
            ret["found"] = True
            ret["claims"] = all_claims
            print(f"⚠️ {domain} has fact-check claims (possible controversy)")
        else:
            print(f"✅ {domain} has no flagged claims in Fact Check API")
        return ret

    except Exception as e:
        print(f"⚠️ Google Fact Check failed: {e}")
        ret["error"] = str(e)
        return ret

# Main checker
def publication_reputation_check(url_or_domain: str, verbose=False):
    domain = _domain_from_url_or_domain(url_or_domain)
    print(f"\n\n🚀 Starting publication reputation check for: {domain}")

    base_score = 0.5   # baseline
    score = base_score
    reasons = []
    signals = {}

    # -------------------------------
    # 1. NewsAPI sources
    newsapi = _newsapi_presence(domain)
    signals["newsapi"] = newsapi
    if newsapi["ok"]:
        if newsapi["present"]:
            score += 0.2
            reasons.append("In NewsAPI source list")
        else:
            reasons.append("Not in NewsAPI sources")
    else:
        reasons.append("NewsAPI unavailable")

    # -------------------------------
    # 2. GNews top headlines
    gnews = _gnews_presence(domain)
    signals["gnews"] = gnews
    if gnews["ok"]:
        if gnews["present"]:
            score += 0.1
            reasons.append("Ranked among GNews headlines")
        else:
            reasons.append("Not in current GNews headlines")
    else:
        reasons.append("GNews unavailable")

    # -------------------------------
    # 3. WHOIS domain age
    age_days = _get_domain_age_days(domain)
    signals["domain_age_days"] = age_days
    if age_days is not None:
        if age_days > 3650:  # >10 years
            score += 0.05
            reasons.append("Domain >10 years old")
        elif age_days < 365:  # <1 year
            score -= 0.1
            reasons.append("Domain <1 year old")
        else:
            reasons.append("Domain age neutral")
    else:
        reasons.append("Domain age unknown")

    # -------------------------------
    # 4. Google Fact Check presence
    fc = _google_fact_check_presence(domain)
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

            print(f"Total fact-checked claims retrieved: {total}")

            if total > 0:
                # credibility ratio: fraction of true claims
                credibility_ratio = true_claims / total

                # Fact-check weight: +/- 0.3
                score += (credibility_ratio - 0.5) * 0.6
                # This means if all claims are true, +0.3; if all false, -0.3
                reasons.append(f"Fact-checked claims: {total}, credibility ratio: {credibility_ratio:.2f}")
            else:
                reasons.append("Fact-checked claims present but no details found")
        else:
            reasons.append("Not in Google Fact Check results (no known controversy)")
    else:
        reasons.append("Google Fact Check unavailable")

    # -------------------------------
    # Clamp score and get label
    score = _clamp(score)
    label = _label(score)

    print(f"\n📊 Final Score: {score:.3f} → {label}")
    print(f"📌 Reasons: {reasons}\n")

    result = {
        "domain": domain,
        "score": round(score, 3),
        "label": label,
        "reasons": reasons,
        "signals": signals,
    }


    # if verbose:
    #     print(json.dumps(result, indent=2))

    return result

# Manual test
# if __name__ == "__main__":
    # test = "https://www.aljazeera.com/news/2025/8/22/world-reacts-as-un-backed-body-declares-famine-in-gaza"
    # publication_reputation_check(test, verbose=True)