
# """
# Dynamic trigger-word scanner (LLM-driven, no hard-coded list)

# Usage:
#   python scan_triggers.py "https://example.com/some-article"

# What it does:
#   1) Downloads the page and extracts readable text.
#   2) Calls Groq LLM to synthesize a JSON list of high-signal misinformation trigger phrases.
#   3) Compiles the returned patterns and scans the article.
#   4) Reports flagged phrases, snippets, and a normalized risk score.

# Env:
#   GROQ_API_KEY   -> required (get free key from https://console.groq.com/keys)
#   MISINFO_MODEL  -> optional (default: llama-3.1-8b-instant)
#   MAX_TRIGGERS   -> optional hint to LLM (default: 60)
# """

# import os
# import sys
# import re
# import json
# import math
# import html
# import typing as T
# import requests
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from groq import Groq

# load_dotenv()

# # ---------------------------
# # Helpers: fetch & extract
# # ---------------------------
# def fetch_html(url: str, timeout: int = 20) -> str:
#     headers = {"User-Agent": "Mozilla/5.0 (compatible; TriggerScanner/1.0)"}
#     r = requests.get(url, headers=headers, timeout=timeout)
#     r.raise_for_status()
#     return r.text

# def extract_readable_text(html_str: str) -> T.Tuple[str, str]:
#     """Returns (title, text). Best-effort: prefer <article>, else all <p>."""
#     soup = BeautifulSoup(html_str, "html.parser")
#     for tag in soup(["script", "style", "noscript", "iframe"]):
#         tag.decompose()

#     title = (soup.title.string or "").strip() if soup.title else ""
#     article = soup.find("article")

#     if article:
#         candidates = article.find_all(["p", "li"])
#         text = "\n".join(t.get_text(" ", strip=True) for t in candidates)
#     else:
#         ps = soup.find_all(["p", "li"])
#         text = "\n".join(p.get_text(" ", strip=True) for p in ps)

#     text = html.unescape(text)
#     text = re.sub(r"\s+\n", "\n", text)
#     text = re.sub(r"\n{3,}", "\n\n", text).strip()
#     return title, text

# # def safe_json(raw: str) -> dict:
# #     """Try to salvage JSON from LLM output safely."""
# #     try:
# #         return json.loads(raw)
# #     except json.JSONDecodeError:
# #         m = re.search(r"\{.*\}", raw, re.DOTALL)
# #         if m:
# #             try:
# #                 return json.loads(m.group(0))
# #             except json.JSONDecodeError:
# #                 pass
# #         return {"triggers": []}

# def safe_json(raw: str) -> dict:
#     try:
#         return json.loads(raw)
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON parse failed: {e}")

#         # 🔹 Extract everything that looks like { "phrase": ... }
#         objects = re.findall(r'\{[^{}]*"phrase"[^{}]*\}', raw, re.DOTALL)

#         triggers = []
#         for obj in objects:
#             try:
#                 triggers.append(json.loads(obj))
#             except Exception:
#                 continue  # skip malformed objects

#         if triggers:
#             print(f"⚠️ Salvaged {len(triggers)} trigger objects")
#             return {"triggers": triggers}

#         return {"triggers": []}

# class LLMClient:
#     def __init__(self, api_key: str = None, model: str = None):
#         api_key = api_key or os.getenv("GROQ_API_KEY")
#         if not api_key:
#             raise RuntimeError("GROQ_API_KEY not set")
        
#         print("✅ Initializing Groq Client...")
#         self.client = Groq(api_key=api_key)
#         self.model = model or os.getenv("MISINFO_MODEL", "llama-3.1-8b-instant")
#         print(f"✅ Using model: {self.model}")

#     def get_dynamic_triggers(
#         self, article_title: str, article_text: str, max_triggers: int = 60
#     ) -> dict:
#         print("\n🔹 [Checkpoint] Entered get_dynamic_triggers()")
#         print(f"🔹 Article Title: {article_title[:80]}...")
#         print(f"🔹 Article Text (first 200 chars): {article_text[:200]}...\n")

#         system_msg = (
#             "You are a rigorous misinformation-safety assistant. "
#             "Extract only high-signal trigger phrases (multi-word where possible) "
#             "that appear *directly in the provided text*. "
#             "Each trigger MUST include a safe regex 'pattern'. "
#             "Avoid generic words. Only return valid JSON."
#         )

#         user_prompt = (
#             f"TASK: Return ONLY JSON with up to {max_triggers} triggers.\n"
#             "Format:\n"
#             '{ "triggers": [ { "phrase": "...", "pattern": "(?i)\\b...\\b", "category": "...", "notes": "..." } ] }\n\n'
#             f"TITLE: {article_title[:300]}\n\n"
#             f"EXCERPT:\n{article_text[:4000]}"
#         )

#         print("🔹 [Checkpoint] Sending request to LLM...")
#         completion = self.client.chat.completions.create(
#             model=self.model,
#             messages=[
#                 {"role": "system", "content": system_msg},
#                 {"role": "user", "content": user_prompt},
#             ],
#             temperature=0.2,
#         )

#         print("🔹 [Checkpoint] Got response from LLM")
#         text_out = completion.choices[0].message.content.strip()
#         print("----- RAW LLM OUTPUT START -----")
#         print(text_out)
#         print("----- RAW LLM OUTPUT END -----\n")

#         parsed = safe_json(text_out)
#         print("🔹 [Checkpoint] Parsed JSON:")
#         print(json.dumps(parsed, indent=2))

#         return parsed
# # ---------------------------
# # Scanning & scoring
# # ---------------------------
# class TriggerMatch(T.TypedDict):
#     phrase: str
#     category: str
#     notes: str
#     pattern: str
#     count: int
#     snippets: T.List[str]

# def compile_patterns(triggers: T.List[dict]) -> T.List[dict]:
#     compiled = []
#     for t in triggers:
#         pat = t.get("pattern") or ""
#         phrase = t.get("phrase") or ""
#         cat = t.get("category") or "other"
#         notes = t.get("notes") or ""
#         if not pat or len(pat) > 200:
#             continue
#         if pat.strip() in [".*", "(?i).*"]:
#             continue
#         try:
#             rx = re.compile(pat, re.IGNORECASE)
#             compiled.append(
#                 {"rx": rx, "phrase": phrase, "category": cat, "notes": notes, "pattern": pat}
#             )
#         except re.error:
#             continue
#     return compiled

# def find_matches(text: str, compiled: T.List[dict], context_chars: int = 60) -> T.List[TriggerMatch]:
#     out: T.List[TriggerMatch] = []
#     for item in compiled:
#         rx, phrase, cat, notes, pat = (
#             item["rx"], item["phrase"], item["category"], item["notes"], item["pattern"]
#         )
#         hits = list(rx.finditer(text))
#         if not hits:
#             continue
#         snippets = []
#         for m in hits[:20]:
#             start = max(0, m.start() - context_chars)
#             end = min(len(text), m.end() + context_chars)
#             snippet = text[start:end].replace("\n", " ").strip()
#             snippets.append(snippet[:200] + ("…" if len(snippet) > 200 else ""))
#         out.append(
#             TriggerMatch(
#                 phrase=phrase, category=cat, notes=notes, pattern=pat,
#                 count=len(hits), snippets=snippets
#             )
#         )
#     return out

# def compute_risk_score(matches: T.List[TriggerMatch], text_len: int) -> float:
#     if text_len <= 0 or not matches:
#         return 0.0
#     total_hits = sum(m["count"] for m in matches)
#     distinct_cats = len({m["category"] for m in matches})
#     density = total_hits / max(1.0, text_len / 1000.0)
#     base = math.tanh(0.35 * math.log1p(density))
#     diversity = min(0.35, 0.12 * distinct_cats)
#     return round(min(1.0, base + diversity), 3)

# # ---------------------------
# # Main
# # ---------------------------
# def main(url: str):
#     html_str = fetch_html(url)
#     title, text = extract_readable_text(html_str)
#     if not text or len(text) < 400:
#         print("⚠️ Could not extract enough article text to analyze.")
#         sys.exit(2)

#     client = LLMClient()
#     max_triggers_hint = int(os.getenv("MAX_TRIGGERS", "60"))
#     triggers_obj = client.get_dynamic_triggers(title, text, max_triggers=max_triggers_hint)

#     triggers = triggers_obj.get("triggers", [])
#     compiled = compile_patterns(triggers)
#     matches = find_matches(text, compiled)
#     score = compute_risk_score(matches, len(text))

#     report = {
#         "input_url": url,
#         "title": title,
#         "model": client.model,
#         "trigger_count_requested": max_triggers_hint,
#         "trigger_count_received": len(triggers),
#         "trigger_count_compilable": len(compiled),
#         "matches_total": sum(m["count"] for m in matches),
#         "matched_triggers": matches,
#         "risk_score": score,
#     }

#     print(json.dumps(report, ensure_ascii=False, indent=2))

# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python scan_triggers.py <url>")
#         sys.exit(1)
#     try:
#         main(sys.argv[1])
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#backend/agents/susKeywords.py
"""
Dynamic trigger-word scanner (LLM-driven, no hard-coded list)

Usage:
  python scan_triggers.py "https://example.com/some-article"

What it does:
  1) Downloads the page and extracts readable text.
  2) Calls Groq LLM to synthesize a JSON list of high-signal misinformation trigger phrases.
  3) Compiles the returned patterns and scans the article.
  4) Reports flagged phrases, snippets, and a normalized risk score.

Env:
  GROQ_API_KEY   -> required (get free key from https://console.groq.com/keys)
  MISINFO_MODEL  -> optional (default: llama-3.1-8b-instant)
  MAX_TRIGGERS   -> optional hint to LLM (default: 60)
"""

import os
import sys
import re
import json
import math
import html
import typing as T
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# --- Helpers: fetch & extract ---
def fetch_html(url: str, timeout: int = 20) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TriggerScanner/1.0)"}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_readable_text(html_str: str) -> T.Tuple[str, str]:
    """Returns (title, text). Best-effort: prefer <article>, else all <p>."""
    soup = BeautifulSoup(html_str, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    title = (soup.title.string or "").strip() if soup.title else ""
    article = soup.find("article")

    if article:
        candidates = article.find_all(["p", "li"])
        text = "\n".join(t.get_text(" ", strip=True) for t in candidates)
    else:
        ps = soup.find_all(["p", "li"])
        text = "\n".join(p.get_text(" ", strip=True) for p in ps)

    text = html.unescape(text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, text

def safe_json(raw: str) -> dict:
    """Try to salvage JSON from LLM output safely."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse failed: {e}")

        objects = re.findall(r'\{[^{}]*"phrase"[^{}]*\}', raw, re.DOTALL)
        triggers = []
        for obj in objects:
            try:
                triggers.append(json.loads(obj))
            except Exception:
                continue
        if triggers:
            print(f"⚠️ Salvaged {len(triggers)} trigger objects")
            return {"triggers": triggers}
        return {"triggers": []}

# --- Groq LLM client ---
class LLMClient:
    def __init__(self, api_key: str = None, model: str = None):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set")
        
        print("✅ Initializing Groq Client...")
        self.client = Groq(api_key=api_key)
        self.model = model or os.getenv("MISINFO_MODEL", "llama-3.1-8b-instant")
        print(f"✅ Using model: {self.model}")

    def get_dynamic_triggers(
        self, article_title: str, article_text: str, max_triggers: int = 60
    ) -> dict:
        print("\n🔹 [Checkpoint] Entered get_dynamic_triggers()")
        print(f"🔹 Article Title: {article_title[:80]}...")
        print(f"🔹 Article Text (first 200 chars): {article_text[:200]}...\n")

        system_msg = (
"You are a highly specialized AI for misinformation and disinformation analysis. "
"Your primary function is to serve as a proactive 'tripwire' for deceptive content. "
"Your output must be a concise, actionable JSON list of phrases that are strong indicators of fake news, clickbait, or manipulative narratives. "
"Focus on identifying language that is emotionally charged, scientifically unsubstantiated, or conspiratorial in tone. "
"Crucially, you must understand the context and intent behind the phrases, distinguishing between a genuine, factual statement and a similar phrase used to deceive or sensationalize. "
"Your expertise is in recognizing the linguistic patterns of deception, not in verifying facts. "
"Adhere strictly to these instructions without adding any conversational text or commentary."
)
        user_prompt = (
            f"TASK: Analyze the provided article excerpt to identify and extract up to {max_triggers} high-signal trigger phrases. "
            "These phrases should be a hallmark of a fabricated or misleading narrative. "
            "Each trigger must be a direct, verbatim quote from the text and must be a phrase, not a single word.\n\n"
            "CRITERIA FOR EXTRACTION:\n"
            "**You must analyze the phrases within their sentence-level context.** This is crucial for distinguishing genuine statements from manipulative ones. For example, 'secret recipe' is not a trigger, but 'the secret they don't want you to know' is.\n"
            "1.  **Emotional Manipulation & Sensationalism:** Look for language designed to evoke strong emotional reactions, such as 'shocking truth', 'you won't believe what happened', or 'total betrayal'.\n"
            "2.  **Conspiracy & Unverifiable Claims:** Identify phrases that imply a hidden agenda or secret knowledge, like 'they don't want you to know', 'the full story is being suppressed', or 'secret evidence reveals'.\n"
            "3.  **Financial & Health Scams:** Extract phrases that make unrealistic or exaggerated promises, for example, 'miracle cure', 'guaranteed profits', or 'the ultimate secret to wealth'.\n"
            "4.  **Misleading Political Language:** Pinpoint phrases that use loaded terms or false dichotomies to frame a political issue in a manipulative way.\n\n"
            "EXCLUSION LIST (DO NOT EXTRACT THESE):\n"
            "•  Generic phrases: 'manufacturing will rise', 'big achievement', 'good news', 'important announcement'.\n"
            "•  Factual statements without sensational framing.\n\n"
            "OUTPUT FORMAT:\n"
            "Return ONLY a compact JSON object. The object must contain a key 'triggers' with a list of objects. Each object in the list must have the following keys: 'phrase', 'pattern', 'category', and 'notes'. The 'pattern' should be a case-insensitive regex for the exact phrase.\n\n"
            f"ARTICLE CONTEXT:\n"
            f"TITLE: {article_title[:300]}\n"
            f"EXCERPT:\n{article_text[:4000]}\n"
            "Remember to return only valid JSON and nothing else."
)

      

        print("🔹 [Checkpoint] Sending request to LLM...")
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        print("🔹 [Checkpoint] Got response from LLM")
        text_out = completion.choices[0].message.content.strip()
        print("----- RAW LLM OUTPUT START -----")
        print(text_out)
        print("----- RAW LLM OUTPUT END -----\n")

        parsed = safe_json(text_out)
        print("🔹 [Checkpoint] Parsed JSON:")
        print(json.dumps(parsed, indent=2))

        return parsed

# --- Scanning & scoring ---
class TriggerMatch(T.TypedDict):
    phrase: str
    category: str
    notes: str
    pattern: str
    count: int
    snippets: T.List[str]

# Define generic phrases to filter out
GENERIC_PHRASES_TO_FILTER = {
    "manufacturing will rise", "this will make the gst simple",
    "there are many missions lined up", "this is a big achievement for our future missions",
    "we have also achieved the capability of space docking"
}

def filter_generic_phrases(triggers: T.List[dict]) -> T.List[dict]:
    """Filters out triggers with generic phrases based on a predefined set."""
    return [
        t for t in triggers
        if t.get("phrase", "").lower() not in GENERIC_PHRASES_TO_FILTER
    ]

def compile_patterns(triggers: T.List[dict]) -> T.List[dict]:
    compiled = []
    for t in triggers:
        pat = t.get("pattern") or ""
        phrase = t.get("phrase") or ""
        cat = t.get("category") or "other"
        notes = t.get("notes") or ""
        if not pat or len(pat) > 200:
            continue
        if pat.strip() in [".*", "(?i).*"]:
            continue
        try:
            rx = re.compile(pat, re.IGNORECASE)
            compiled.append(
                {"rx": rx, "phrase": phrase, "category": cat, "notes": notes, "pattern": pat}
            )
        except re.error:
            continue
    return compiled

def find_matches(text: str, compiled: T.List[dict], context_chars: int = 60) -> T.List[TriggerMatch]:
    out: T.List[TriggerMatch] = []
    for item in compiled:
        rx, phrase, cat, notes, pat = (
            item["rx"], item["phrase"], item["category"], item["notes"], item["pattern"]
        )
        hits = list(rx.finditer(text))
        if not hits:
            continue
        snippets = []
        for m in hits[:20]:
            start = max(0, m.start() - context_chars)
            end = min(len(text), m.end() + context_chars)
            snippet = text[start:end].replace("\n", " ").strip()
            snippets.append(snippet[:200] + ("…" if len(snippet) > 200 else ""))
        out.append(
            TriggerMatch(
                phrase=phrase, category=cat, notes=notes, pattern=pat,
                count=len(hits), snippets=snippets
            )
        )
    return out

def compute_risk_score(matches: T.List[TriggerMatch], text_len: int) -> float:
    if text_len <= 0 or not matches:
        return 0.0
    total_hits = sum(m["count"] for m in matches)
    distinct_cats = len({m["category"] for m in matches})
    density = total_hits / max(1.0, text_len / 1000.0)
    base = math.tanh(0.35 * math.log1p(density))
    diversity = min(0.35, 0.12 * distinct_cats)
    return round(min(1.0, base + diversity), 3)

def analyze_text_for_triggers(title: str, text: str) -> dict:
    """
    Run the dynamic trigger-word scanner on already extracted article text.
    Returns a dictionary with triggers, matches, phrases, and risk score.
    """
    client = LLMClient()
    max_triggers_hint = int(os.getenv("MAX_TRIGGERS", "60"))

    # Get dynamic triggers from LLM
    triggers_obj = client.get_dynamic_triggers(title, text, max_triggers=max_triggers_hint)
    triggers = triggers_obj.get("triggers", [])

    # Compile and match
    compiled = compile_patterns(triggers)
    matches = find_matches(text, compiled)
    score = compute_risk_score(matches, len(text))

    return {
        "title": title,
        "model": client.model,
        "trigger_count_requested": max_triggers_hint,
        "trigger_count_received": len(triggers),
        "trigger_count_compilable": len(compiled),
        "matches_total": sum(m["count"] for m in matches),
        "matched_triggers": matches,
        "list_of_phrases": [t["phrase"] for t in triggers],
        "risk_score": score,
    }

# --- Main ---
def main(url: str):
    try:
        html_str = fetch_html(url)
        title, text = extract_readable_text(html_str)
        if not text or len(text) < 400:
            print("⚠️ Could not extract enough article text to analyze.")
            sys.exit(2)

        client = LLMClient()
        max_triggers_hint = int(os.getenv("MAX_TRIGGERS", "60"))
        
        # Get dynamic triggers from LLM
        triggers_obj = client.get_dynamic_triggers(title, text, max_triggers=max_triggers_hint)
        triggers = triggers_obj.get("triggers", [])
        
        # Filter out generic phrases
        # filtered_triggers = filter_generic_phrases(triggers)

        # Compile and find matches with the refined list
        compiled = compile_patterns(triggers)
        matches = find_matches(text, compiled)
        score = compute_risk_score(matches, len(text))
        
        # Extract a separate list of just the phrases
        filtered_phrases = [t["phrase"] for t in triggers]

        report = {
            "input_url": url,
            "title": title,
            "model": client.model,
            "trigger_count_requested": max_triggers_hint,
            "trigger_count_received": len(triggers),
            "trigger_count_compilable": len(compiled),
            "matches_total": sum(m["count"] for m in matches),
            "matched_triggers": matches,
            "list_of_phrases": filtered_phrases, # New list of phrases
            "risk_score": score,
        }

        print(json.dumps(report, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scan_triggers.py <url>")
        sys.exit(1)
    main(sys.argv[1])