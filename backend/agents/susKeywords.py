
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
from rapidfuzz import fuzz, process

import typing as T
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

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
"From the input article text, extract and return only the exact phrases present in the text "
"that are strong indicators of fake news, clickbait, or manipulative narratives. "
"Do not invent or suggest phrases that are not in the input. "
"Your output must be a concise, actionable JSON list of these phrases. "
"Focus on language that is emotionally charged, scientifically unsubstantiated, or conspiratorial in tone. "
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
            "Pick the 10 strongest manipulative or misleading ones that clearly show intent, prefer longer contextual phrases over short buzzwords." 
            " At least 7 words long (longer contextual fragments preferred).\n"
            "Return ONLY a compact JSON object. The object must contain a key 'triggers' with a list of objects. Each object in the list must have the following keys: 'phrase', 'pattern', 'category', and 'notes'. The 'pattern' should be a case-insensitive regex for the exact phrase.\n\n"
            f"ARTICLE CONTEXT:\n"
            f"TITLE: {article_title[:300]}\n"
            f"EXCERPT:\n{article_text[:4000]}\n"
            "Remember to return only valid JSON and nothing else."
            "Do not invent or rephrase; extract only phrases that appear exactly in the article text."
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

  
    long_phrases = [t for t in triggers if len(t.get("phrase", "").split()) >= 7]

    top_phrases = long_phrases[:5]

    # Extract snippets from text for each phrase
    results = []
    # for t in top_phrases:
    #     phrase = t.get("phrase", "")
    #     idx = text.lower().find(phrase.lower())
    #     if idx != -1:
    #         start = max(0, idx - 60)
    #         end = min(len(text), idx + len(phrase) + 60)
    #         snippet = text[start:end].replace("\n", " ").strip()
    #         results.append({"phrase": phrase, "snippet": snippet})
     
    for t in top_phrases:
        phrase = t.get("phrase", "")
        snippet = ""
        if phrase:
            # Exact match
            idx = text.lower().find(phrase.lower())
            if idx != -1:
                start = max(0, idx - 60)
                end = min(len(text), idx + len(phrase) + 60)
                snippet = text[start:end].replace("\n", " ").strip()
            else:
                # Fuzzy match
                match = process.extractOne(phrase, [text], scorer=fuzz.partial_ratio)
                if match and match[1] > 75:  # similarity threshold
                    idx = text.lower().find(match[0].lower().split()[0])
                    if idx != -1:
                        start = max(0, idx - 60)
                        end = min(len(text), idx + len(phrase) + 60)
                        snippet = text[start:end].replace("\n", " ").strip()
        
        if snippet:  # only keep if a real snippet was found
            results.append({"phrase": phrase, "snippet": snippet})
            
        deduped = []
        for r in sorted(results, key=lambda x: -len(x["phrase"])):
            if not any(r["phrase"].lower() in d["phrase"].lower() for d in deduped):
                deduped.append(r)

        # Keep only top 5
        results = deduped[:5]
       


    return {
        "title": title,
        "model": client.model,
        "trigger_count_requested": max_triggers_hint,
        "trigger_count_received": len(triggers),
        
        "list_of_phrases": results,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scan_triggers.py <url>")
        sys.exit(1)
    main(sys.argv[1])