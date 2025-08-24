# # agents/credibility-context/source_check.py

# import whois
# import requests
# import datetime
# import tldextract

# # Example local list of unreliable domains
# UNRELIABLE_SITES = {"fakenews.com", "clickbaitnews.org"}

# def get_domain_age(domain):
#     try:
#         w = whois.whois(domain)
#         if isinstance(w.creation_date, list):
#             creation_date = w.creation_date[0]
#         else:
#             creation_date = w.creation_date
#         if creation_date:
#             return (datetime.datetime.now() - creation_date).days
#     except Exception:
#         return None

# def has_https(url):
#     return url.startswith("https://")

# def check_source(url):
#     domain = tldextract.extract(url).top_domain_under_public_suffix
    
#     age_days = get_domain_age(domain)
#     https_ok = has_https(url)
#     listed_bad = domain in UNRELIABLE_SITES

#     # Simple rules for credibility
#     if listed_bad:
#         credibility = "High Risk / Disinformation"
#     elif age_days is not None and age_days < 180:
#         credibility = "Suspicious (new domain)"
#     elif not https_ok:
#         credibility = "Suspicious (no HTTPS)"
#     else:
#         credibility = "Likely Trustworthy"
    
#     return {
#         "domain": domain,
#         "age_days": age_days,
#         "https": https_ok,
#         "known_disinfo": listed_bad,
#         "credibility": credibility
#     }

# if __name__ == "__main__":
#     test_url = "https://www.bbc.com/news"
#     print(check_source(test_url))


# #!/usr/bin/env python3
# """
# agents/credibility-context/source_check.py

# Improved Source Credibility Checker
# - Accepts a URL or local file path as input (CLI) OR uses a hardcoded default if none provided
# - Loads an optional unreliable_domains.json from the same folder
# - Performs: domain extraction, whois (age), HTTPS check, DNS resolve
# - Produces a JSON report saved as credibility_report_<basename>.json in the output directory
# """

# import argparse
# import os
# import json
# import datetime
# import socket
# import re
# import sys

# # Optional libraries (script will still run if network/whois libs missing; notes will be in JSON)
# try:
#     import tldextract
# except Exception:
#     tldextract = None

# try:
#     import whois
# except Exception:
#     whois = None

# try:
#     import requests
# except Exception:
#     requests = None

# # -------------------- CONFIG --------------------
# # Default input used when you run `python source_check.py` with no argument.
# # Change this to any URL or local file path you prefer.
# DEFAULT_INPUT = "https://www.bbc.com/news"

# # If there's an unreliable_domains.json in the same folder as this script, it will be used.
# FALLBACK_UNRELIABLE = [
#     "fakenews.com",
#     "clickbaitnews.org",
#     "example-fake-site.test"
# ]

# # Output directory (relative to current working directory) when -o not provided
# DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "credibility_reports")

# # -------------------- Helpers --------------------
# def load_unreliable_list(script_dir):
#     path = os.path.join(script_dir, "unreliable_domains.json")
#     if os.path.exists(path):
#         try:
#             with open(path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#             domains = set()
#             if isinstance(data, list):
#                 for item in data:
#                     if isinstance(item, str):
#                         domains.add(item.lower().strip())
#                     elif isinstance(item, dict) and "domain" in item:
#                         domains.add(item["domain"].lower().strip())
#             return domains
#         except Exception as e:
#             print(f"Warning: could not load unreliable_domains.json: {e}", file=sys.stderr)
#     return set(FALLBACK_UNRELIABLE)

# def extract_domain_from_url_or_path(value):
#     # If it's a file path, return basename (without extension)
#     if os.path.exists(value) and os.path.isfile(value):
#         return os.path.splitext(os.path.basename(value))[0], "file"
#     # Else assume it's a URL; try tldextract then fallback
#     if tldextract:
#         try:
#             ext = tldextract.extract(value)
#             domain = ext.top_domain_under_public_suffix or ext.registered_domain or ""
#             if domain:
#                 return domain.lower(), "url"
#         except Exception:
#             pass
#     # fallback simple parse
#     try:
#         if "://" in value:
#             value = value.split("://",1)[1]
#         value = value.split("/",1)[0]
#         value = value.split(":",1)[0]
#         return value.lower(), "url"
#     except Exception:
#         return value.lower(), "unknown"

# def find_first_url_in_file(path):
#     try:
#         with open(path, "r", encoding="utf-8", errors="ignore") as f:
#             text = f.read(100000)
#     except Exception:
#         return None
#     urls = re.findall(r"https?://[^\s'\"<>]+", text)
#     return urls[0] if urls else None

# def get_domain_age_days(domain):
#     if not whois:
#         return None, "whois library not available"
#     try:
#         w = whois.whois(domain)
#         creation_date = None
#         if hasattr(w, "creation_date"):
#             cd = w.creation_date
#             if isinstance(cd, list):
#                 creation_date = cd[0] if cd else None
#             else:
#                 creation_date = cd
#         if isinstance(creation_date, str):
#             try:
#                 creation_date = datetime.datetime.fromisoformat(creation_date)
#             except Exception:
#                 creation_date = None
#         if isinstance(creation_date, datetime.datetime):
#             delta = (datetime.datetime.now() - creation_date).days
#             return delta, None
#         return None, "creation_date not found"
#     except Exception as e:
#         return None, f"whois error: {e}"

# def check_https(url_or_domain):
#     https_flag = str(url_or_domain).lower().startswith("https://")
#     if not requests:
#         return https_flag, "requests library not available"
#     try:
#         target = url_or_domain if "://" in url_or_domain else f"https://{url_or_domain}"
#         try:
#             r = requests.head(target, timeout=6, allow_redirects=True, verify=True)
#         except Exception:
#             r = requests.get(target, timeout=6, allow_redirects=True, verify=True)
#         https_flag = True
#         return https_flag, None
#     except requests.exceptions.SSLError as e:
#         return False, f"SSL error: {e}"
#     except Exception as e:
#         return https_flag, f"request error: {e}"

# def dns_resolves(domain):
#     try:
#         ip = socket.gethostbyname(domain)
#         return True, ip
#     except Exception as e:
#         return False, str(e)

# def compute_credibility_label(domain, age_days, https_ok, known_bad):
#     score = 0
#     reasons = []
#     if known_bad:
#         reasons.append("Listed in unreliable domains list")
#         score -= 50
#     if age_days is None:
#         reasons.append("Domain age unknown")
#     else:
#         if age_days < 180:
#             reasons.append("Domain is very new (<180 days)")
#             score -= 20
#         elif age_days < 365*2:
#             reasons.append("Domain is relatively new (<2 years)")
#             score -= 5
#         else:
#             score += 10
#     if https_ok:
#         score += 5
#     else:
#         reasons.append("No valid HTTPS or HTTPS check failed")
#         score -= 10
#     if score <= -30:
#         label = "High Risk / Disinformation"
#     elif score <= 0:
#         label = "Suspicious"
#     else:
#         label = "Likely Trustworthy"
#     return label, score, reasons

# # -------------------- Main --------------------
# def main():
#     parser = argparse.ArgumentParser(description="Source Credibility Check - URL or file path input")
#     # make the input argument optional; if not provided, use DEFAULT_INPUT
#     parser.add_argument("input", nargs="?", default=DEFAULT_INPUT, help="URL or local file path to analyze (optional)")
#     parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory to write report JSON")
#     args = parser.parse_args()

#     input_val = args.input
#     output_dir = args.output_dir
#     os.makedirs(output_dir, exist_ok=True)

#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     unreliable_set = load_unreliable_list(script_dir)

#     parsed, kind = extract_domain_from_url_or_path(input_val)

#     derived_url = None
#     if kind == "file":
#         maybe = find_first_url_in_file(input_val)
#         if maybe:
#             derived_url = maybe
#             parsed, _ = extract_domain_from_url_or_path(derived_url)

#     report = {
#         "input": input_val,
#         "detected_type": kind,
#         "parsed_domain_or_name": parsed,
#         "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
#         "checks": {}
#     }

#     known_bad = parsed.lower() in unreliable_set
#     report["checks"]["known_unreliable"] = known_bad

#     age_days, whois_note = get_domain_age_days(parsed)
#     report["checks"]["domain_age_days"] = age_days
#     if whois_note:
#         report["checks"]["domain_age_note"] = whois_note

#     https_target = derived_url if derived_url else input_val if kind == "url" else parsed
#     https_ok, https_note = check_https(https_target)
#     report["checks"]["https"] = https_ok
#     if https_note:
#         report["checks"]["https_note"] = https_note

#     dns_ok, dns_info = dns_resolves(parsed)
#     report["checks"]["dns_resolves"] = dns_ok
#     report["checks"]["dns_info"] = dns_info

#     report["checks"]["unreliable_list_size"] = len(unreliable_set)
#     report["checks"]["unreliable_sample"] = list(unreliable_set)[:10]

#     label, score, reasons = compute_credibility_label(parsed, age_days, https_ok, known_bad)
#     report["credibility_label"] = label
#     report["credibility_score"] = score
#     report["credibility_reasons"] = reasons

#     safe_name = parsed.replace(".", "_").replace("/", "_")
#     out_filename = os.path.join(output_dir, f"credibility_report_{safe_name}.json")
#     with open(out_filename, "w", encoding="utf-8") as f:
#         json.dump(report, f, indent=2, ensure_ascii=False)

#     print("Wrote report to:", out_filename)
#     print(json.dumps({
#         "file": out_filename,
#         "domain": parsed,
#         "label": label,
#         "score": score
#     }, indent=2))

# if __name__ == "__main__":
#     main()









# #!/usr/bin/env python3
# """
# source_check.py — Enhanced Source Credibility Checker

# Features:
# - Uses unreliable_domains.json and fact_checks.json (local)
# - WHOIS domain age, HTTPS, DNS checks
# - Wayback availability + CDX fallback for archival history
# - Optional Google Fact Check API lookup (requires env GOOGLE_API_KEY)
# - Auto-update facts via DataCommons ClaimReview feed (tries multiple endpoints)
# - Outputs a JSON report per-run with detailed reasons
# """

# import argparse
# import os
# import json
# import datetime
# import socket
# import re
# import sys
# import time
# import urllib.parse

# # Optional libs
# try:
#     import tldextract
# except Exception:
#     tldextract = None

# try:
#     import whois
# except Exception:
#     whois = None

# try:
#     import requests
# except Exception:
#     requests = None

# # ---------------- CONFIG ----------------
# DEFAULT_INPUT = "https://www.bbc.com/news"
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# OUTPUT_DIR = os.path.join(os.getcwd(), "credibility_reports")
# UNRELIABLE_JSON = os.path.join(SCRIPT_DIR, "unreliable_domains.json")
# FACTCHECKS_JSON = os.path.join(SCRIPT_DIR, "fact_checks.json")

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)
# GOOGLE_FACTCHECK_ENDPOINT = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# # Wayback endpoints
# WAYBACK_AVAIL = "http://archive.org/wayback/available?url={}"   # availability endpoint
# WAYBACK_CDX = "http://web.archive.org/cdx/search/cdx?url={url}&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest&limit=1&sort=ascending"

# # Candidate auto-update feeds (tries in order)
# DATACOMMONS_ENDPOINTS = [
#     "https://www.datacommons.org/factcheck/download",  # official page (often redirects)
#     "https://raw.githubusercontent.com/datacommonsorg/misc-data/main/factchecks/fact_checks.json"  # GitHub mirror (works often)
# ]

# # ---------------- Helpers ----------------
# def try_json_get(url, timeout=30):
#     if not requests:
#         raise RuntimeError("requests not installed")
#     r = requests.get(url, timeout=timeout)
#     r.raise_for_status()
#     # try to decode JSON (some feeds may return JSON-LD / wrapped dict)
#     return r.json()

# def update_factchecks():
#     """Attempt to fetch ClaimReview feed from several known endpoints and save fact_checks.json"""
#     if not requests:
#         print("requests not available; cannot update fact checks.", file=sys.stderr)
#         return False, "requests-missing"
#     last_err = None
#     for url in DATACOMMONS_ENDPOINTS:
#         try:
#             print("Trying feed:", url)
#             data = try_json_get(url, timeout=30)
#             if isinstance(data, dict) and "claims" in data and isinstance(data["claims"], list):
#                 claims = data["claims"]
#             elif isinstance(data, list):
#                 claims = data
#             elif isinstance(data, dict):
#                 # some endpoints may return { "items": [...] } or similar — try to find list value
#                 for v in data.values():
#                     if isinstance(v, list):
#                         claims = v
#                         break
#                 else:
#                     claims = []
#             else:
#                 claims = []
#             if claims:
#                 with open(FACTCHECKS_JSON, "w", encoding="utf-8") as f:
#                     json.dump(claims, f, indent=2, ensure_ascii=False)
#                 print(f"Updated {FACTCHECKS_JSON} with {len(claims)} entries (from {url})")
#                 return True, {"source": url, "count": len(claims)}
#             else:
#                 last_err = f"no list-like claims found at {url}"
#                 print(last_err, file=sys.stderr)
#         except Exception as e:
#             last_err = str(e)
#             print(f"Failed to fetch {url}: {e}", file=sys.stderr)
#             time.sleep(1)
#     return False, {"error": last_err}

# def load_json_list(path):
#     if os.path.exists(path):
#         try:
#             with open(path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#             if isinstance(data, list):
#                 return data
#             # if top-level dict, try to find a list field
#             if isinstance(data, dict):
#                 for v in data.values():
#                     if isinstance(v, list):
#                         return v
#         except Exception as e:
#             print(f"Warning: failed to load {path}: {e}", file=sys.stderr)
#     return []

# def load_unreliable_domains():
#     data = load_json_list(UNRELIABLE_JSON)
#     domains = set()
#     for item in data:
#         if isinstance(item, str):
#             domains.add(item.lower().strip())
#         elif isinstance(item, dict) and "domain" in item:
#             domains.add(item["domain"].lower().strip())
#     return domains

# def extract_domain(value):
#     # If local file path, return basename
#     if os.path.exists(value) and os.path.isfile(value):
#         return os.path.splitext(os.path.basename(value))[0]
#     if tldextract:
#         try:
#             ext = tldextract.extract(value)
#             dom = ext.top_domain_under_public_suffix or ext.registered_domain or ""
#             if dom:
#                 return dom.lower()
#         except Exception:
#             pass
#     try:
#         parsed = urllib.parse.urlparse(value)
#         host = parsed.netloc or value
#         host = host.split(":")[0]
#         return host.lower().lstrip("www.")
#     except Exception:
#         return value.lower()

# def find_urls_in_obj(obj):
#     urls = set()
#     if isinstance(obj, str):
#         urls.update(re.findall(r"https?://[^\s'\"<>]+", obj))
#     elif isinstance(obj, dict):
#         for v in obj.values():
#             urls.update(find_urls_in_obj(v))
#     elif isinstance(obj, list):
#         for it in obj:
#             urls.update(find_urls_in_obj(it))
#     return urls

# def count_local_debunks(domain, factchecks):
#     domain = domain.lower().lstrip("www.")
#     hits = 0
#     sources = []
#     for entry in factchecks:
#         for u in find_urls_in_obj(entry):
#             try:
#                 host = urllib.parse.urlparse(u).netloc.lower().lstrip("www.")
#                 if host.endswith(domain) or domain.endswith(host):
#                     hits += 1
#                     sources.append(entry.get("url") if isinstance(entry, dict) else u)
#                     break
#             except Exception:
#                 continue
#     return hits, list(set(sources))

# # Wayback availability then CDX fallback for earliest capture
# def wayback_availability(url_or_domain):
#     if not requests:
#         return {"note": "requests not available"}
#     try:
#         q = urllib.parse.quote(url_or_domain, safe="")
#         r = requests.get(WAYBACK_AVAIL.format(q), timeout=8)
#         if r.status_code != 200:
#             return {"note": f"availability returned {r.status_code}"}
#         data = r.json().get("archived_snapshots", {})
#         if "closest" in data:
#             c = data["closest"]
#             return {"available": True, "timestamp": c.get("timestamp"), "url": c.get("url"), "source": "availability"}
#         return {"available": False}
#     except Exception as e:
#         return {"note": f"availability error: {e}"}

# def wayback_cdx_first(domain):
#     if not requests:
#         return {"note": "requests not available"}
#     try:
#         url = WAYBACK_CDX.format(url=urllib.parse.quote(domain, safe=""))
#         r = requests.get(url, timeout=10)
#         if r.status_code != 200:
#             return {"note": f"cdx returned {r.status_code}"}
#         # CDX sometimes returns JSON array; parse carefully
#         try:
#             data = r.json()
#             # first row may be header or actual data depending on endpoint parameters
#             if isinstance(data, list) and len(data) >= 1:
#                 first = data[0]
#                 # If the first element looks like a header (strings 'timestamp' etc.), check next
#                 if isinstance(first, list) and len(first) >= 2:
#                     ts, orig = first[0], first[1]
#                     iso = None
#                     try:
#                         iso = datetime.datetime.strptime(ts, "%Y%m%d%H%M%S").isoformat() + "Z"
#                     except Exception:
#                         pass
#                     return {"available": True, "first_capture_ts": ts, "first_capture_iso": iso, "first_capture_url": orig, "source": "cdx"}
#         except ValueError:
#             # non-json text fallback parsing
#             text = r.text.strip().splitlines()
#             if text:
#                 parts = text[0].split()
#                 if len(parts) >= 2:
#                     ts, orig = parts[0], parts[1]
#                     return {"available": True, "first_capture_ts": ts, "first_capture_url": orig, "source": "cdx"}
#         return {"available": False}
#     except Exception as e:
#         return {"note": f"cdx error: {e}"}

# def wayback_info(input_val):
#     # Try availability endpoint first (works well for exact URLs)
#     a = wayback_availability(input_val)
#     if isinstance(a, dict) and a.get("available"):
#         return a
#     # Fallback to domain-level CDX
#     domain = extract_domain(input_val)
#     c = wayback_cdx_first(domain)
#     if isinstance(c, dict) and c.get("available"):
#         return c
#     # return availability result (which may include notes)
#     return a

# # WHOIS, HTTPS, DNS helpers
# def get_domain_age_days(domain):
#     if not whois:
#         return None, "whois not installed"
#     try:
#         w = whois.whois(domain)
#         cd = getattr(w, "creation_date", None)
#         if isinstance(cd, list):
#             cd = cd[0] if cd else None
#         if isinstance(cd, datetime.datetime):
#             return (datetime.datetime.now() - cd).days, None
#         # sometimes string parse
#         if isinstance(cd, str):
#             try:
#                 dt = datetime.datetime.fromisoformat(cd)
#                 return (datetime.datetime.now() - dt).days, None
#             except Exception:
#                 pass
#         return None, "creation_date not found"
#     except Exception as e:
#         return None, f"whois error: {e}"

# def check_https(url_or_domain):
#     https_flag = str(url_or_domain).lower().startswith("https://")
#     if not requests:
#         return https_flag, "requests not available"
#     try:
#         target = url_or_domain if "://" in url_or_domain else f"https://{url_or_domain}"
#         # HEAD then GET fallback
#         try:
#             r = requests.head(target, timeout=6, allow_redirects=True, verify=True)
#         except Exception:
#             r = requests.get(target, timeout=6, allow_redirects=True, verify=True)
#         return True, None
#     except requests.exceptions.SSLError as e:
#         return False, f"SSL error: {e}"
#     except Exception as e:
#         return False, f"request error: {e}"

# def dns_resolves(domain):
#     try:
#         ip = socket.gethostbyname(domain)
#         return True, ip
#     except Exception as e:
#         return False, str(e)

# # Optional Google FactCheck search (per-domain, requires key)
# def google_factcheck_search(domain, api_key):
#     if not requests:
#         return {"note": "requests not available"}
#     if not api_key:
#         return {"note": "no API key provided"}
#     try:
#         params = {"query": domain, "key": api_key, "pageSize": 10}
#         r = requests.get(GOOGLE_FACTCHECK_ENDPOINT, params=params, timeout=8)
#         if r.status_code != 200:
#             return {"note": f"google api returned {r.status_code}", "content": r.text}
#         data = r.json()
#         claims = data.get("claims", [])
#         sources = []
#         for c in claims:
#             cr = c.get("claimReview")
#             if isinstance(cr, list) and cr:
#                 url = cr[0].get("url")
#             else:
#                 url = c.get("url")
#             if url:
#                 sources.append(url)
#         return {"count": len(claims), "sources": sources}
#     except Exception as e:
#         return {"note": f"google api error: {e}"}

# # Scoring rules (heuristic)
# def compute_final_score(age_days, https_ok, known_bad, wayback_available, local_debunks, google_hits):
#     score = 0
#     reasons = []
#     # age
#     if age_days is None:
#         reasons.append("Domain age unknown")
#     else:
#         if age_days < 90:
#             score -= 20
#             reasons.append("Domain very new (<90 days)")
#         elif age_days < 365:
#             score -= 5
#         elif age_days >= 365*2:
#             score += 10
#     # https
#     if https_ok:
#         score += 5
#     else:
#         score -= 10
#         reasons.append("No valid HTTPS")
#     # wayback
#     if wayback_available:
#         score += 5
#     else:
#         score -= 3
#         reasons.append("No wayback archival evidence")
#     # known unreliable
#     if known_bad:
#         score -= 60
#         reasons.append("Listed in local unreliable domains list")
#     # local debunks
#     if local_debunks and local_debunks > 0:
#         penalty = -10 * min(local_debunks, 6)
#         score += penalty
#         reasons.append(f"{local_debunks} local fact-check hits")
#     # google hits
#     if isinstance(google_hits, dict) and google_hits.get("count", 0) > 0:
#         gm = google_hits["count"]
#         penalty = -12 * min(gm, 6)
#         score += penalty
#         reasons.append(f"{gm} Google fact-check matches")
#     score = max(-100, min(100, score))
#     if score <= -30:
#         label = "High Risk / Disinformation"
#     elif score <= 0:
#         label = "Suspicious"
#     else:
#         label = "Likely Trustworthy"
#     return label, score, reasons

# # ---------------- Main ----------------
# def main():
#     parser = argparse.ArgumentParser(description="Source Credibility Checker")
#     parser.add_argument("--update-factchecks", action="store_true", help="Fetch ClaimReview feed and update fact_checks.json")
#     parser.add_argument("input", nargs="?", default=DEFAULT_INPUT, help="URL or local file (optional)")
#     parser.add_argument("-o", "--output-dir", default=OUTPUT_DIR, help="Output folder for report JSON")
#     args = parser.parse_args()

#     if args.update_factchecks:
#         ok, info = update_factchecks()
#         if not ok:
#             print("Auto-update failed:", info, file=sys.stderr)
#         return

#     os.makedirs(args.output_dir, exist_ok=True)
#     input_val = args.input
#     domain = extract_domain(input_val).lstrip("www.").lower()

#     unreliable_set = load_unreliable_domains()
#     local_factchecks = load_json_list(FACTCHECKS_JSON)

#     report = {"input": input_val, "parsed_domain_or_name": domain, "timestamp": datetime.datetime.utcnow().isoformat() + "Z", "checks": {}}

#     known_bad = domain in unreliable_set
#     report["checks"]["known_unreliable"] = known_bad
#     report["checks"]["unreliable_list_size"] = len(unreliable_set)
#     report["checks"]["unreliable_sample"] = list(unreliable_set)[:10]

#     age_days, whois_note = get_domain_age_days(domain)
#     report["checks"]["domain_age_days"] = age_days
#     if whois_note: report["checks"]["domain_age_note"] = whois_note

#     https_ok, https_note = check_https(input_val if input_val.startswith("http") else domain)
#     report["checks"]["https"] = https_ok
#     if https_note: report["checks"]["https_note"] = https_note

#     dns_ok, dns_info = dns_resolves(domain)
#     report["checks"]["dns_resolves"] = dns_ok
#     report["checks"]["dns_info"] = dns_info

#     wb = wayback_info(input_val)
#     # if availability returned false, try domain-level CDX fallback
#     if isinstance(wb, dict) and not wb.get("available", False) and ("note" in wb or True):
#         wb = wayback_info(domain)
#     report["checks"]["wayback"] = wb
#     wayback_available = bool(wb.get("available"))

#     debunk_count, debunk_sources = count_local_debunks(domain, local_factchecks)
#     report["checks"]["local_factcheck_debunk_count"] = debunk_count
#     report["checks"]["local_factcheck_sources"] = debunk_sources

#     google_hits = google_factcheck_search(domain, GOOGLE_API_KEY) if GOOGLE_API_KEY else {"note": "GOOGLE_API_KEY not set; skipped"}
#     report["checks"]["google_factcheck"] = google_hits

#     label, score, reasons = compute_final_score(age_days, https_ok, known_bad, wayback_available, debunk_count, google_hits)
#     report["credibility_label"] = label
#     report["credibility_score"] = score
#     report["credibility_reasons"] = reasons

#     # output file
#     safe = domain.replace(".", "_").replace("/", "_")
#     outp = os.path.join(args.output_dir, f"credibility_report_{safe}.json")
#     with open(outp, "w", encoding="utf-8") as f:
#         json.dump(report, f, indent=2, ensure_ascii=False)

#     print("Wrote report to:", outp)
#     print(json.dumps({"domain": domain, "label": label, "score": score, "debunk_count": debunk_count}, indent=2))


# if __name__ == "__main__":
#     main()










#!/usr/bin/env python3
"""
source_check.py — Credibility checker with tiered scoring, robust HTTPS check,
and recommended actions.

What’s inside:
- Domain extraction
- WHOIS domain age + simple registrant-privacy heuristic
- HTTPS reachability (robust: HEAD→GET, counts TLS success even on 4xx/5xx)
- DNS resolution
- MX/SPF/DMARC checks (if dnspython installed)
- Wayback availability + CDX fallback
- Local fact-check matching (fact_checks.json)
- Scoring → Tiered labels (label == tier) + Confidence + Recommended Action
- Explainable per-feature deltas

Usage:
  python source_check.py "https://example.com"
Outputs JSON to ./credibility_reports/credibility_report_<domain>.json
"""

import argparse
import os
import json
import datetime
import socket
import re
import sys
import traceback
import urllib.parse

# Optional libraries (set to None when missing)
try:
    import tldextract
except Exception:
    tldextract = None

try:
    import whois
except Exception:
    whois = None

try:
    import requests
except Exception:
    requests = None

# dnspython resolver (for MX/SPF/DMARC checks)
try:
    import dns.resolver as dns_resolver
except Exception:
    dns_resolver = None

# ---------------- Configuration ----------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT = "https://www.bbc.com/news"
OUTPUT_DIR = os.path.join(os.getcwd(), "credibility_reports")
UNRELIABLE_JSON = os.path.join(SCRIPT_DIR, "unreliable_domains.json")
FACTCHECKS_JSON = os.path.join(SCRIPT_DIR, "fact_checks.json")

WAYBACK_AVAIL = "http://archive.org/wayback/available?url={}"
WAYBACK_CDX = (
    "http://web.archive.org/cdx/search/cdx"
    "?url={url}&output=json&fl=timestamp,original&filter=statuscode:200"
    "&collapse=digest&limit=1&sort=ascending"
)

# ---------------- Small utilities ----------------
def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)

def load_json(path):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
    except Exception as e:
        print(f"Warning: failed to load JSON {path}: {e}", file=sys.stderr)
    return None

# ---------------- Domain extraction ----------------
def extract_domain(value):
    """Return normalized domain for a URL or filename."""
    if os.path.exists(value) and os.path.isfile(value):
        return os.path.splitext(os.path.basename(value))[0]
    if tldextract:
        try:
            ext = tldextract.extract(value)
            dom = ext.top_domain_under_public_suffix or ext.registered_domain or ""
            if dom:
                return dom.lower().lstrip("www.")
        except Exception:
            pass
    try:
        p = urllib.parse.urlparse(value)
        host = p.netloc or value
        host = host.split(":")[0]
        return host.lower().lstrip("www.")
    except Exception:
        return value.lower()

# ---------------- Load lists ----------------
def load_unreliable_domains():
    data = load_json(UNRELIABLE_JSON)
    if not data:
        return set()
    domains = set()
    for item in data:
        if isinstance(item, str):
            domains.add(item.lower().strip())
        elif isinstance(item, dict) and "domain" in item:
            domains.add(item["domain"].lower().strip())
    return domains

def load_local_factchecks():
    data = load_json(FACTCHECKS_JSON)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                return v
    return []

# ---------------- WHOIS helpers ----------------
def get_domain_age_days(domain):
    """Return (age_days, note)."""
    if not whois:
        return None, "whois not installed"
    try:
        w = whois.whois(domain)
        cd = getattr(w, "creation_date", None)
        if isinstance(cd, list):
            cd = cd[0] if cd else None
        if isinstance(cd, datetime.datetime):
            return (datetime.datetime.now() - cd).days, None
        if isinstance(cd, str):
            try:
                dt = datetime.datetime.fromisoformat(cd)
                return (datetime.datetime.now() - dt).days, None
            except Exception:
                pass
        return None, "creation_date not found"
    except Exception as e:
        return None, f"whois error: {e}"

def detect_registrant_privacy(domain):
    """Heuristic: detect privacy-protected WHOIS entries."""
    if not whois:
        return None, "whois not installed"
    try:
        w = whois.whois(domain)
        text = str(w).lower()
        indicators = [
            "whoisguard", "redacted", "privacy",
            "contact privacy", "domains by proxy", "privacy service"
        ]
        for ind in indicators:
            if ind in text:
                return True, f"found '{ind}' in whois"
        return False, None
    except Exception as e:
        return None, f"whois error: {e}"

# ---------------- DNS / email auth ----------------
def dns_resolves(domain):
    try:
        ip = socket.gethostbyname(domain)
        return True, ip
    except Exception as e:
        return False, str(e)

def check_mx_spf_dmarc(domain):
    """Return dict: has_mx, has_spf, has_dmarc, notes."""
    res = {"has_mx": None, "has_spf": None, "has_dmarc": None, "notes": []}
    if dns_resolver is None:
        res["notes"].append("dnspython not installed")
        return res
    # MX
    try:
        dns_resolver.resolve(domain, "MX", lifetime=5)
        res["has_mx"] = True
    except Exception:
        res["has_mx"] = False
    # SPF via TXT
    try:
        txts = dns_resolver.resolve(domain, "TXT", lifetime=5)
        found_spf = False
        for r in txts:
            try:
                raw = b"".join(r.strings).decode() if hasattr(r, "strings") else str(r)
            except Exception:
                raw = str(r)
            if "v=spf1" in raw.lower():
                found_spf = True
                break
        res["has_spf"] = found_spf
    except Exception:
        res["has_spf"] = False
    # DMARC
    try:
        dns_resolver.resolve("_dmarc." + domain, "TXT", lifetime=5)
        res["has_dmarc"] = True
    except Exception:
        res["has_dmarc"] = False
    return res

# ---------------- HTTPS check (robust) ----------------
def check_https(url_or_domain):
    """
    Return (https_ok_bool, note).
    Success criteria: we can complete a TLS connection and receive any HTTP response
    (2xx/3xx/4xx/5xx) over HTTPS. HEAD is tried, then GET. Redirects are followed.
    Only SSL/connection errors count as HTTPS=False.
    """
    target = url_or_domain if "://" in url_or_domain else f"https://{url_or_domain}"
    if not requests:
        # Fall back to scheme sniff; not ideal but better than nothing
        return target.lower().startswith("https://"), "requests not installed (heuristic result)"

    try:
        s = requests.Session()
        s.max_redirects = 5
        # Try HEAD first
        try:
            r = s.head(target, timeout=8, allow_redirects=True, verify=True)
            # If we got here without SSL error, HTTPS works, even if 404/403/500
            if r.url.lower().startswith("https://"):
                return True, f"HTTPS reachable (HEAD {r.status_code})"
        except Exception as e_head:
            head_err = str(e_head)
            # Try GET as fallback (some servers block HEAD)
            try:
                r = s.get(target, timeout=10, allow_redirects=True, verify=True)
                if r.url.lower().startswith("https://"):
                    return True, f"HTTPS reachable (GET {r.status_code}; HEAD failed: {head_err[:120]})"
            except requests.exceptions.SSLError as e_ssl:
                return False, f"SSL error: {e_ssl}"
            except requests.exceptions.ConnectionError as e_conn:
                return False, f"Connection error: {e_conn}"
            except Exception as e_get:
                return False, f"HTTPS GET error: {e_get}"

        # If HEAD succeeded but final URL is not HTTPS (rare), treat as failure
        return False, f"Reached non-HTTPS endpoint after redirects: {r.url}"
    except requests.exceptions.SSLError as e:
        return False, f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {e}"
    except Exception as e:
        return False, f"HTTPS check error: {e}"

# ---------------- Wayback helpers ----------------
def wayback_availability(url_or_domain):
    if not requests:
        return {"note": "requests not installed"}
    try:
        q = urllib.parse.quote(url_or_domain, safe="")
        r = requests.get(WAYBACK_AVAIL.format(q), timeout=8)
        if r.status_code != 200:
            return {"note": f"availability returned {r.status_code}"}
        data = r.json()
        snaps = data.get("archived_snapshots", {})
        if "closest" in snaps and snaps["closest"]:
            c = snaps["closest"]
            return {"available": True, "timestamp": c.get("timestamp"), "url": c.get("url"), "source": "availability"}
        return {"available": False, "source": "availability"}
    except Exception as e:
        return {"note": f"availability error: {e}"}

def wayback_cdx_first(domain):
    if not requests:
        return {"note": "requests not installed"}
    try:
        url = WAYBACK_CDX.format(url=urllib.parse.quote(domain, safe=""))
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {"note": f"cdx returned {r.status_code}"}
        try:
            data = r.json()
            if isinstance(data, list) and len(data) >= 1:
                first = data[0]
                if isinstance(first, list) and len(first) >= 2:
                    ts, orig = first[0], first[1]
                    iso = None
                    try:
                        iso = datetime.datetime.strptime(ts, "%Y%m%d%H%M%S").isoformat() + "Z"
                    except Exception:
                        iso = None
                    return {"available": True, "first_capture_ts": ts, "first_capture_iso": iso, "first_capture_url": orig, "source": "cdx"}
        except ValueError:
            lines = r.text.strip().splitlines()
            if lines:
                parts = lines[0].split()
                if len(parts) >= 2:
                    ts, orig = parts[0], parts[1]
                    return {"available": True, "first_capture_ts": ts, "first_capture_url": orig, "source": "cdx-text"}
        return {"available": False, "source": "cdx"}
    except Exception as e:
        return {"note": f"cdx error: {e}"}

def wayback_info(input_val):
    avail = wayback_availability(input_val)
    if isinstance(avail, dict) and avail.get("available"):
        return avail
    # fallback to domain-level CDX
    domain = extract_domain(input_val)
    cdx = wayback_cdx_first(domain)
    if isinstance(cdx, dict) and cdx.get("available"):
        return cdx
    return avail

# ---------------- Local fact-check matching ----------------
def find_urls_in_obj(obj):
    urls = set()
    if isinstance(obj, str):
        urls.update(re.findall(r"https?://[^\s'\"<>]+", obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            urls.update(find_urls_in_obj(v))
    elif isinstance(obj, list):
        for it in obj:
            urls.update(find_urls_in_obj(it))
    return urls

def count_local_debunks(domain, factchecks):
    domain = domain.lower().lstrip("www.")
    hits = 0
    sources = []
    for entry in factchecks:
        for u in find_urls_in_obj(entry):
            try:
                host = urllib.parse.urlparse(u).netloc.lower().lstrip("www.")
                if host.endswith(domain) or domain.endswith(host):
                    hits += 1
                    sources.append(entry.get("url", u) if isinstance(entry, dict) else u)
                    break
            except Exception:
                continue
    return hits, list(set(sources))

# ---------------- Scoring, tiers, actions ----------------
def compute_verbose_score_with_tiers(age_days, https_ok, known_bad, wayback_available, local_debunks, mxspf):
    """
    Returns:
      label (== tier), score [-100,100], reasons, explain, tier, confidence
    """
    score = 0
    explain = {}

    # Age
    if age_days is None:
        explain["age"] = {"value": None, "delta": 0, "note": "unknown age"}
    else:
        if age_days < 90:
            explain["age"] = {"value": age_days, "delta": -20, "note": "very new (<90d)"}
            score -= 20
        elif age_days < 365:
            explain["age"] = {"value": age_days, "delta": -5, "note": "young (<1y)"}
            score -= 5
        elif age_days >= 365 * 2:
            explain["age"] = {"value": age_days, "delta": +10, "note": "older (>2y)"}
            score += 10
        else:
            explain["age"] = {"value": age_days, "delta": 0, "note": "neutral age"}

    # HTTPS
    if https_ok:
        explain["https"] = {"value": True, "delta": +5, "note": "HTTPS reachable"}
        score += 5
    else:
        explain["https"] = {"value": False, "delta": -10, "note": "HTTPS unreachable (TLS/connection error)"}
        score -= 10

    # Wayback
    if wayback_available:
        explain["wayback"] = {"value": True, "delta": +5, "note": "Wayback archival evidence"}
        score += 5
    else:
        explain["wayback"] = {"value": False, "delta": -3, "note": "No Wayback evidence"}
        score -= 3

    # Known unreliable
    if known_bad:
        explain["known_unreliable"] = {"value": True, "delta": -60, "note": "Flagged by local unreliable list"}
        score -= 60
    else:
        explain["known_unreliable"] = {"value": False, "delta": 0, "note": "Not flagged locally"}

    # MX/SPF/DMARC
    if isinstance(mxspf, dict):
        mx = mxspf.get("has_mx")
        spf = mxspf.get("has_spf")
        dmarc = mxspf.get("has_dmarc")
        delta = 0
        notes = []
        if mx is False:
            delta -= 8; notes.append("no MX")
        if spf is False:
            delta -= 4; notes.append("no SPF")
        if dmarc is False:
            delta -= 2; notes.append("no DMARC")
        explain["email_auth"] = {
            "value": {"mx": mx, "spf": spf, "dmarc": dmarc},
            "delta": delta,
            "note": "; ".join(notes) if notes else "email auth present"
        }
        score += delta
    else:
        explain["email_auth"] = {"value": None, "delta": 0, "note": "email auth check skipped"}

    # Local debunks
    if local_debunks and local_debunks > 0:
        delta = -10 * min(local_debunks, 6)
        explain["local_debunks"] = {"value": local_debunks, "delta": delta, "note": "local fact-check hits"}
        score += delta
    else:
        explain["local_debunks"] = {"value": 0, "delta": 0, "note": "no local fact-checks"}

    # Clamp
    score = max(-100, min(100, score))

    # Tiers (and set label == tier)
    if score >= 60:
        tier = "Very High Trust"
    elif score >= 30:
        tier = "High Trust"
    elif score >= 10:
        tier = "Moderate Trust"
    elif score >= 0:
        tier = "Mixed / Needs Review"
    elif score >= -29:
        tier = "Low Trust"
    else:
        tier = "Very Low / High Risk"
    label = tier

    # Confidence: simple |score|/100
    confidence = min(1.0, max(0.0, abs(score) / 100.0))

    # Reasons: negative notes
    reasons = [f"{k}: {v.get('note')}" for k, v in explain.items() if v.get('delta', 0) < 0]

    return label, score, reasons, explain, tier, confidence

def map_recommended_action(tier, confidence):
    """
    Map tier + confidence to a suggested action:
      - auto_show
      - show_with_warning
      - queue_for_review
      - suppress
    """
    if tier in ("Very High Trust", "High Trust"):
        return "auto_show"
    if tier == "Moderate Trust":
        return "auto_show" if confidence >= 0.5 else "show_with_warning"
    if tier == "Mixed / Needs Review":
        return "queue_for_review"
    if tier == "Low Trust":
        return "show_with_warning" if confidence < 0.4 else "queue_for_review"
    # Very Low / High Risk
    return "suppress" if confidence >= 0.3 else "queue_for_review"

# ---------------- Main ----------------
def main():
    parser = argparse.ArgumentParser(description="Credibility checker with tiers, HTTPS robustness, and recommended actions")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT, help="URL or domain to evaluate")
    parser.add_argument("-o", "--output-dir", default=OUTPUT_DIR, help="Output directory for JSON reports")
    args = parser.parse_args()

    try:
        os.makedirs(args.output_dir, exist_ok=True)
        input_val = args.input
        domain = extract_domain(input_val).lstrip("www.").lower()

        unreliable = load_unreliable_domains()
        factchecks = load_local_factchecks()

        report = {
            "input": input_val,
            "parsed_domain_or_name": domain,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checks": {}
        }

        # Known unreliable
        known_bad = domain in unreliable
        report["checks"]["known_unreliable"] = known_bad
        report["checks"]["unreliable_list_size"] = len(unreliable)
        report["checks"]["unreliable_sample"] = list(unreliable)[:10]

        # Domain age
        age_days, age_note = get_domain_age_days(domain)
        report["checks"]["domain_age_days"] = age_days
        if age_note:
            report["checks"]["domain_age_note"] = age_note

        # Registrant privacy
        priv, priv_note = detect_registrant_privacy(domain)
        report["checks"]["registrant_privacy"] = priv
        if priv_note:
            report["checks"]["registrant_privacy_note"] = priv_note

        # HTTPS
        https_ok, https_note = check_https(input_val if input_val.startswith("http") else domain)
        report["checks"]["https"] = https_ok
        if https_note:
            report["checks"]["https_note"] = https_note

        # DNS
        dns_ok, dns_info = dns_resolves(domain)
        report["checks"]["dns_resolves"] = dns_ok
        report["checks"]["dns_info"] = dns_info

        # MX / SPF / DMARC
        mxspf = check_mx_spf_dmarc(domain)
        report["checks"]["email_auth"] = mxspf

        # Wayback
        wb = wayback_info(input_val)
        if isinstance(wb, dict) and not wb.get("available", False):
            wb = wayback_info(domain)
        report["checks"]["wayback"] = wb
        wayback_available = bool(wb.get("available"))

        # Local fact-checks
        debunk_count, debunk_sources = count_local_debunks(domain, factchecks)
        report["checks"]["local_factcheck_debunk_count"] = debunk_count
        report["checks"]["local_factcheck_sources"] = debunk_sources

        # Compute final score + tier + confidence
        label, score, reasons, explain, tier, confidence = compute_verbose_score_with_tiers(
            age_days, https_ok, known_bad, wayback_available, debunk_count, mxspf
        )

        # Recommended action
        recommended_action = map_recommended_action(tier, confidence)

        report["credibility_label"] = label         # equals tier
        report["credibility_score"] = score
        report["credibility_reasons"] = reasons
        report["explain"] = explain
        report["credibility_tier"] = tier
        report["credibility_confidence"] = round(confidence, 3)
        report["recommended_action"] = recommended_action

        # Save JSON report
        safe = domain.replace(".", "_").replace("/", "_")
        outp = os.path.join(args.output_dir, f"credibility_report_{safe}.json")
        save_json(outp, report)

        # Print concise summary + per-feature deltas
        print("Wrote report to:", outp)
        print(json.dumps({
            "domain": domain,
            "label": label,
            "score": score,
            "tier": tier,
            "confidence": round(confidence, 3),
            "recommended_action": recommended_action
        }, indent=2))
        print("\nExplainability (feature -> delta):")
        for k, v in explain.items():
            print(f"- {k}: delta={v.get('delta')}, note={v.get('note')}, value={v.get('value')}")
    except Exception:
        print("Unhandled exception during run:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(2)

if __name__ == "__main__":
    main()
