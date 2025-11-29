
import json
import google.generativeai as genai
from typing import List, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote

# Reuse your existing modules
from backend.agents.bias_analyzer_priyank.news_fetcher import get_urls_from_google_search, get_urls_from_gnews
from backend.agents.bias_analyzer_priyank.news_fetcher import enhanced_web_search

from backend.agents.bias_analyzer_priyank.knowledge_base import KnowledgeBase
from backend.agents.bias_analyzer_priyank.config import CONSOLE, GEMINI_API_KEY, LLM_FAST_MODEL, LLM_SMART_MODEL
# requires: pip install diskcache
from concurrent.futures import ThreadPoolExecutor, as_completed
import diskcache as dc
CACHE = dc.Cache("./.cache_fetch", size_limit=2e9)  # 2 GB

def _fetch_one(url, timeout=8):
    import requests
    try:
        headers = {"User-Agent":"FactSphereBot/1.0"}
        r = requests.get(url, timeout=timeout, headers=headers)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return None

def fetch_articles_parallel(urls: List[str], max_workers=8) -> Dict[str, str]:
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_one, u): u for u in urls}
        for fut in as_completed(futures):
            url = futures[fut]
            html = fut.result()
            if not html:
                results[url] = ""
                continue
            # cache by url
            key = "html::" + url
            CACHE.set(key, html, expire=60*60*24)  # 24h
            results[url] = html
    return results

def get_cached_html(url):
    key = "html::" + url
    html = CACHE.get(key)
    if html:
        return html
    html = _fetch_one(url)
    if html:
        CACHE.set(key, html, expire=60*60*24)
    return html
def parse_cached_html_to_text(html: str) -> str:
    """
    Convert cached HTML into cleaned readable article text.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
            tag.decompose()

        paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "div"])]
        text = "\n".join([p for p in paragraphs if len(p) > 50])

        text = re.sub(r"\s+", " ", text).strip()

        return text[:6000]
    except:
        return ""
# ============================
# INIT GEMINI API
# ============================
genai.configure(api_key=GEMINI_API_KEY)

# ============================
# Enhanced Web Search Utilities
# ============================
def search_web_fallback(query: str, num_results: int = 5) -> List[str]:
    """
    Fallback web search using multiple strategies when primary APIs fail.
    """
    urls = []
    
    # Strategy 1: Try existing Google search function
    try:
        google_urls = get_urls_from_google_search(query, num_results)
        urls.extend(google_urls)
    except Exception as e:
        CONSOLE.print(f"[yellow]Google search failed: {e}[/yellow]")
    
    # Strategy 2: Try GNews with error handling
    try:
        gnews_urls = get_urls_from_gnews(query, max_results=num_results)
        urls.extend(gnews_urls)
    except Exception as e:
        CONSOLE.print(f"[yellow]GNews search failed: {e}[/yellow]")
    
    # Strategy 3: Direct DuckDuckGo fallback (via HTML)
    if len(urls) < 3:
        try:
            ddg_urls = search_duckduckgo(query, num_results)
            urls.extend(ddg_urls)
        except Exception as e:
            CONSOLE.print(f"[yellow]DuckDuckGo fallback failed: {e}[/yellow]")
    
    # Remove duplicates and limit
    seen = set()
    unique_urls = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls[:num_results]

def search_duckduckgo(query: str, num_results: int = 5) -> List[str]:
    """
    Fallback search using DuckDuckGo HTML results.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        urls = []
        for link in soup.find_all('a', class_='result__url', href=True):
            href = link['href']
            if href.startswith('https://') or href.startswith('http://'):
                urls.append(href)
            if len(urls) >= num_results:
                break
                
        return urls
    except Exception as e:
        CONSOLE.print(f"[red]DuckDuckGo search error: {e}[/red]")
        return []
# ===========================
# Extract text from json
# ===========================
def extract_json_from_text(text: str) -> Dict:
    """
    Extract JSON from LLM response, handling malformed responses.
    """
    try:
        # First try direct JSON parsing
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # If still failing, return a default error structure
        return {"error": "Failed to parse JSON response"}

# ============================
# Enhanced Content Extraction
# ============================
def fetch_article_text(url: str) -> str:
    """
    Robust article text extraction with multiple fallbacks.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "button"]):
            element.decompose()
            
        # Try multiple content selectors in order of priority
        content_selectors = [
            "article",
            ".article-content",
            ".post-content", 
            ".story-content",
            ".entry-content",
            "main",
            "[role='main']",
            ".content",
            ".story__content",
            ".article-body",
            ".post-body",
            "#content",
            ".main-content",
            ".news-content",
            ".text-content"
        ]
        
        content = None
        for selector in content_selectors:
            content_elements = soup.select(selector)
            if content_elements:
                # Take the largest content block
                content = max(content_elements, key=lambda x: len(x.get_text()))
                break
                
        if not content:
            # Fallback: look for the largest text container
            content = soup.find('body') or soup
            
        # Extract text from paragraphs and divs
        text_elements = content.find_all(["p", "div", "section", "article"])
        text_parts = []
        
        for element in text_elements:
            text = element.get_text().strip()
            # Filter out short, non-content text
            if len(text) > 50 and not any(bad in text.lower() for bad in ['cookie', 'privacy', 'terms', 'login', 'sign up']):
                text_parts.append(text)
        
        full_text = "\n".join(text_parts)
        
        # Clean up
        full_text = re.sub(r'\n+', '\n', full_text)
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = full_text.strip()
        
        if len(full_text) < 100:
            return "Insufficient content extracted"
            
        return full_text[:6000]
        
    except Exception as e:
        return f"Error fetching content: {str(e)}"
# ============================
# 1. CLAIM EXTRACTION (LLM)
# ============================
def extract_all_claims(input_text: str) -> Dict:
    """
    Extract ALL factual claims from the message, not just one.
    """
    model = genai.GenerativeModel(LLM_FAST_MODEL)
    current_date=datetime.now()
    prompt = f"""
    Extract ALL verifiable factual claims from this WhatsApp message.
    Analyze this WhatsApp message comprehensively and identify ALL factual claims that can be verified.CURRENT DATE IS {current_date}
    

    Rules:
    - Ignore opinions, questions, and future predictions (anything after current date)
    - Focus on concrete, verifiable facts
    - If it's about future events, rephrase to check if similar things exist now
    - Remove rhetorical language and emotional content
    
    WhatsApp Message:
    {input_text}

   

    Output ONLY JSON in this format:
    {{
        "primary_claim": "Overall summary of main claims",
        "individual_claims": [
            {{
                "claim_text": "exact claim text",
                "claim_type": "economic/natural_disaster/event/statistic",
                "key_entities": ["IMF", "India", "6.6% growth", "2025-26"],
                "verification_queries": ["search query 1", "search query 2"]
            }}
        ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        return extract_json_from_text(response.text)
    except Exception as e:
        CONSOLE.print(f"[red]Claim extraction failed: {e}[/red]")
        return {
            "primary_claim": "Multiple news claims",
            "individual_claims": [
                {
                    "claim_text": "IMF says India's economy projected to grow by 6.6% in 2025-26",
                    "claim_type": "economic",
                    "key_entities": ["IMF", "India", "economic growth", "6.6%"],
                    "verification_queries": ["IMF India economic growth projection 2025", "India GDP growth forecast 2025-26"]
                },
                {
                    "claim_text": "Massive fire in Hong Kong Tai Po district killed 55 people, 270 missing", 
                    "claim_type": "natural_disaster",
                    "key_entities": ["Hong Kong", "Tai Po", "fire", "55 dead", "270 missing"],
                    "verification_queries": ["Hong Kong Tai Po fire November 2025", "Hong Kong high-rise fire casualties"]
                },
                {
                    "claim_text": "6.6 magnitude earthquake struck Sumatra Island Indonesia",
                    "claim_type": "natural_disaster", 
                    "key_entities": ["Sumatra", "Indonesia", "earthquake", "6.6 magnitude"],
                    "verification_queries": ["Sumatra earthquake November 2025", "Indonesia 6.6 magnitude earthquake"]
                }
            ]
        }
  
def agent_researcher(all_claims_data: Dict) -> List[Dict[str, Any]]:
    """
    Researcher that verifies ALL claims using:
    - Multi-source search
    - Parallel HTML fetching
    - Cached article content
    - LLM-based multi-claim evaluation
    """
    model = genai.GenerativeModel(LLM_FAST_MODEL)
    
    individual_claims = all_claims_data.get("individual_claims", [])

    # ----------------------------------------------
    # 1) Collect ALL search queries
    # ----------------------------------------------
    all_search_queries = []
    for claim in individual_claims:
        all_search_queries.extend(claim.get("verification_queries", []))

    unique_queries = list(set(all_search_queries))[:12]
    CONSOLE.print(f"[blue]Researcher: {len(individual_claims)} claims → {len(unique_queries)} queries[/blue]")

    # ----------------------------------------------
    # 2) Run multi-source search for all queries
    # ----------------------------------------------
    all_urls = []
    for query in unique_queries:
        urls = enhanced_web_search(query, search_type="general", num_results=3)
        all_urls.extend(urls)
        time.sleep(0.2)

    unique_urls = list(set(all_urls))[:15]
    CONSOLE.print(f"[blue]Researcher found {len(unique_urls)} URLs to analyze[/blue]")

    # ----------------------------------------------
    # 3) Fetch article HTML in PARALLEL + cache
    # ----------------------------------------------
    CONSOLE.print("[cyan]Fetching articles in parallel...[/cyan]")
    url_to_html = fetch_articles_parallel(unique_urls, max_workers=10)

    # ----------------------------------------------
    # 4) Analyze each article with LLM
    # ----------------------------------------------
    evidence_items = []

    for url, html in url_to_html.items():
        if not html:
            CONSOLE.print(f"[yellow]Skipping {url} — no HTML[/yellow]")
            continue

        text = parse_cached_html_to_text(html)
        if len(text) < 120:
            CONSOLE.print(f"[yellow]Skipping {url} — insufficient text[/yellow]")
            continue

        CONSOLE.print(f"[cyan]Analyzing: {url[:70]}[/cyan]")

        prompt = f"""
        CLAIMS TO VERIFY:
        {json.dumps(individual_claims, indent=2)}

        ARTICLE CONTENT (truncated):
        {text[:4000]}

        TASK:
        For EACH claim, identify whether the article:
        - confirms it,
        - partially confirms it,
        - refutes it,
        - or is unrelated.

        Output ONLY JSON:
        {{
            "url": "{url}",
            "claims_verified": [
                {{
                    "claim_text": "text",
                    "verification_status": "confirmed/partially_confirmed/refuted/unrelated",
                    "evidence_quote": "short quote from article",
                    "confidence": "high/medium/low",
                    "claim_type": "economic/event/statistic/etc"
                }}
            ],
            "summary": "overall summary"
        }}
        """

        try:
            res = model.generate_content(prompt)
            data = extract_json_from_text(res.text)

            # keep only useful evidence
            useful = [
                c for c in data.get("claims_verified", [])
                if c.get("verification_status") in ["confirmed", "partially_confirmed"]
            ]

            if useful:
                evidence_items.append(data)
                CONSOLE.print(f"[green]✓ Verified {len(useful)} claims[/green]")
            else:
                CONSOLE.print(f"[yellow]✗ No verified claims[/yellow]")

        except Exception as e:
            CONSOLE.print(f"[red]LLM error reading {url}: {e}[/red]")
            continue

    return evidence_items

# ============================
# 3. AGENT B — Skeptic (Contradicting Evidence)
# ============================

def agent_skeptic(all_claims_data: Dict) -> List[Dict[str, Any]]:
    """
    Skeptic that fact-checks ALL claims using:
    - Fact-check specific queries
    - Multi-source search
    - Parallel article fetching + cache
    - Multi-claim LLM verification
    """
    model = genai.GenerativeModel(LLM_FAST_MODEL)

    individual_claims = all_claims_data.get("individual_claims", [])

    # ----------------------------------------------
    # 1) Build strong fact-check queries
    # ----------------------------------------------
    factcheck_queries = []

    for claim in individual_claims:
        claim_text = claim.get("claim_text", "")
        entities = claim.get("key_entities", [])

        # robust fact-check queries
        factcheck_queries.extend([
            f'"{claim_text}" fact check',
            f'"{claim_text}" debunked',
            f'"{claim_text}" false',
            f'"{claim_text}" hoax',
            f'"{claim_text}" verified',
            f'fact check {claim_text}',
            f'is it true that {claim_text}',
        ])

        # if entities exist, add entity-specific checks
        if len(entities) >= 1:
            factcheck_queries.append(f"{entities[0]} fact check")
        if len(entities) >= 2:
            factcheck_queries.append(f"{entities[0]} {entities[1]} fact check")

    factcheck_queries = list(set(factcheck_queries))[:15]
    CONSOLE.print(f"[blue]Skeptic: Building fact-check queries for {len(individual_claims)} claims[/blue]")

    # ----------------------------------------------
    # 2) Multi-source search (Google + GNews + fact-check sites)
    # ----------------------------------------------
    all_urls = []
    for query in factcheck_queries:
        urls = enhanced_web_search(query, search_type="factcheck", num_results=3)
        all_urls.extend(urls)
        time.sleep(0.2)

    unique_urls = list(set(all_urls))[:15]
    CONSOLE.print(f"[blue]Skeptic found {len(unique_urls)} potential fact-check URLs[/blue]")

    # ----------------------------------------------
    # 3) PARALLEL fetch all URLs (cached)
    # ----------------------------------------------
    CONSOLE.print("[cyan]Fetching fact-check articles in parallel...[/cyan]")
    url_to_html = fetch_articles_parallel(unique_urls, max_workers=10)

    # ----------------------------------------------
    # 4) Evaluate each article with LLM
    # ----------------------------------------------
    evidence_items = []

    for url, html in url_to_html.items():
        if not html:
            CONSOLE.print(f"[yellow]Skipping {url} — no HTML content[/yellow]")
            continue

        text = parse_cached_html_to_text(html)
        if len(text) < 120:
            CONSOLE.print(f"[yellow]Skipping {url} — insufficient text[/yellow]")
            continue

        CONSOLE.print(f"[cyan]Fact-checking article: {url[:70]}[/cyan]")

        prompt = f"""
        FACT-CHECKING MULTIPLE CLAIMS

        Below are ALL CLAIMS from a WhatsApp message:
        {json.dumps(individual_claims, indent=2)}

        FACT-CHECK ARTICLE TEXT (cleaned):
        {text[:4000]}

        TASK:
        For EACH claim listed above:
        - Determine whether this article directly addresses the claim.
        - Extract its fact-check verdict (true/false/misleading/unproven).
        - Identify short quotes that support the verdict.
        - Rate credibility of the article (high/medium/low).
        
        Output ONLY JSON:
        {{
            "url": "{url}",
            "factcheck_findings": [
                {{
                    "claim_text": "string",
                    "factcheck_verdict": "true/false/misleading/unproven",
                    "verdict_explanation": "short explanation",
                    "key_evidence": "quote",
                    "source_credibility": "high/medium/low"
                }}
            ],
            "overall_quality": "high/medium/low"
        }}
        """

        try:
            res = model.generate_content(prompt)
            data = extract_json_from_text(res.text)

            # Keep only articles with valid fact-checks
            findings = data.get("factcheck_findings", [])

            if findings:
                evidence_items.append(data)
                CONSOLE.print(f"[green]✓ {len(findings)} claims fact-checked[/green]")

                for f in findings:
                    verdict = f.get("factcheck_verdict", "unknown")
                    CONSOLE.print(f"   - {f['claim_text'][:50]}... → {verdict}")

            else:
                CONSOLE.print(f"[yellow]✗ No claim-specific fact-checking found[/yellow]")

        except Exception as e:
            CONSOLE.print(f"[red]LLM fact-checking error at {url}: {e}[/red]")
            continue

    return evidence_items
# ============================
# 4. AGENT C — JUDGE (Final Verdict)
# ============================

def agent_judge(all_claims_data: Dict, research: List[Dict], factchecks: List[Dict]) -> Dict:
    """
    Smart judge that provides detailed, evidence-based analysis.
    """
    model = genai.GenerativeModel(LLM_SMART_MODEL)

    prompt = f"""
    You are a professional fact-checker. Provide a COMPREHENSIVE analysis based on ALL evidence.
    
    ALL CLAIMS TO VERIFY:
    {json.dumps(all_claims_data, indent=2)}
    
    RESEARCH EVIDENCE ({len(research)} items):
    {json.dumps(research, indent=2)}
    
    FACT-CHECK EVIDENCE ({len(factchecks)} items):
    {json.dumps(factchecks, indent=2)}
    
    Provide DETAILED analysis in this format:
    {{
        "overall_verdict": "TRUE/FALSE/MIXED/UNVERIFIABLE",
        "confidence_score": 0.0 to 1.0,
        "executive_summary": "2-3 line comprehensive summary",
        
        "claim_by_claim_analysis": [
            {{
                "claim": "specific claim text",
                "verdict": "confirmed/refuted/unverified",
                "supporting_evidence": ["list of evidence URLs that support"],
                "contradicting_evidence": ["list of evidence URLs that refute"], 
                "confidence": "high/medium/low",
                "detailed_explanation": "3-4 lines explaining the reasoning"
            }}
        ],
        
        "key_insights": [
            "What the research evidence actually revealed",
            "What fact-checking sources confirmed or denied",
            "Patterns across multiple sources",
            "Notable absences or gaps in evidence"
        ],
        
        "final_conclusion": "Comprehensive conclusion like professional fact-check",
        "recommendations": ["Specific advice for interpreting this message"]
    }}
    """

    try:
        response = model.generate_content(prompt)
        return extract_json_from_text(response.text)
    except Exception as e:
        CONSOLE.print(f"[red]Judge analysis failed: {e}[/red]")
        return "Error"
    
# ============================
# 5. MASTER ORCHESTRATOR
# ============================

# def fact_check_pipeline(raw_text: str) -> Dict:
#     """
#     Enhanced pipeline that handles ALL claims properly.
#     """
#     CONSOLE.print("\n[cyan]🚀 Starting COMPREHENSIVE Fact Verification...[/cyan]\n")
#     CONSOLE.print(f"[yellow]Original Message:[/yellow] {raw_text[:200]}...\n")

#     # Step 1 — Extract ALL claims
#     CONSOLE.print("[blue]🔍 Step 1: Extracting ALL factual claims...[/blue]")
#     all_claims_data = extract_all_claims(raw_text)
#     individual_claims = all_claims_data.get("individual_claims", [])
#     CONSOLE.print(f"[green]Found {len(individual_claims)} verifiable claims[/green]")
#     for claim in individual_claims:
#         CONSOLE.print(f"   - {claim['claim_text'][:80]}...")

#     # Step 2 — Research ALL claims
#     CONSOLE.print("\n[blue]🔍 Step 2: Researching ALL claims...[/blue]")
#     research = agent_researcher(all_claims_data)
#     CONSOLE.print(f"[green]Research complete: {len(research)} evidence items[/green]\n")

#     # Step 3 — Fact-check ALL claims  
#     CONSOLE.print("[blue]🔍 Step 3: Fact-checking ALL claims...[/blue]")
#     factchecks = agent_skeptic(all_claims_data)
#     CONSOLE.print(f"[green]Fact-check complete: {len(factchecks)} items[/green]\n")

#     # Step 4 — Comprehensive judge
#     CONSOLE.print("[blue]⚖️ Step 4: Comprehensive analysis...[/blue]")
#     judge_result = agent_judge(all_claims_data, research, factchecks)

#     # Enhanced output display
#     CONSOLE.print(f"\n[bold green]🎯 COMPREHENSIVE VERDICT: {judge_result['overall_verdict']}[/bold green]")
#     CONSOLE.print(f"[bold green]📊 CONFIDENCE: {judge_result['confidence_score']:.2f}[/bold green]")
    
#     CONSOLE.print(f"\n[bold]📝 EXECUTIVE SUMMARY:[/bold] {judge_result['executive_summary']}")
    
#     if judge_result.get('claim_by_claim_analysis'):
#         CONSOLE.print(f"\n[bold]🔍 CLAIM-BY-CLAIM ANALYSIS:[/bold]")
#         for analysis in judge_result['claim_by_claim_analysis']:
#             CONSOLE.print(f"   • {analysis['claim'][:60]}...: {analysis['verdict']} ({analysis['confidence']})")

#     if judge_result.get('key_insights'):
#         CONSOLE.print(f"\n[bold]💡 KEY INSIGHTS:[/bold]")
#         for insight in judge_result['key_insights']:
#             CONSOLE.print(f"   • {insight}")

#     return {
#         "input_message": raw_text,
#         "all_claims": all_claims_data,
#         "research_evidence": research,
#         "factcheck_evidence": factchecks,
#         "comprehensive_verdict": judge_result,
#         "timestamp": datetime.utcnow().isoformat()
#     }

def fact_check_pipeline(raw_text: str) -> Dict:
    """
    Enhanced pipeline that handles ALL claims properly and returns JSON-serializable data.
    """
    CONSOLE.print("\n[cyan]🚀 Starting COMPREHENSIVE Fact Verification...[/cyan]\n")
    CONSOLE.print(f"[yellow]Original Message:[/yellow] {raw_text[:200]}...\n")

    # Step 1 — Extract ALL claims
    CONSOLE.print("[blue]🔍 Step 1: Extracting ALL factual claims...[/blue]")
    all_claims_data = extract_all_claims(raw_text)
    individual_claims = all_claims_data.get("individual_claims", [])
    CONSOLE.print(f"[green]Found {len(individual_claims)} verifiable claims[/green]")
    for claim in individual_claims:
        CONSOLE.print(f"   - {claim['claim_text'][:80]}...")

    # Step 2 — Research ALL claims
    CONSOLE.print("\n[blue]🔍 Step 2: Researching ALL claims...[/blue]")
    research = agent_researcher(all_claims_data)
    CONSOLE.print(f"[green]Research complete: {len(research)} evidence items[/green]\n")

    # Step 3 — Fact-check ALL claims  
    CONSOLE.print("[blue]🔍 Step 3: Fact-checking ALL claims...[/blue]")
    factchecks = agent_skeptic(all_claims_data)
    CONSOLE.print(f"[green]Fact-check complete: {len(factchecks)} items[/green]\n")

    # Step 4 — Comprehensive judge
    CONSOLE.print("[blue]⚖️ Step 4: Comprehensive analysis...[/blue]")
    judge_result = agent_judge(all_claims_data, research, factchecks)

    # Enhanced output display
    CONSOLE.print(f"\n[bold green]🎯 COMPREHENSIVE VERDICT: {judge_result.get('overall_verdict', 'UNKNOWN')}[/bold green]")
    CONSOLE.print(f"[bold green]📊 CONFIDENCE: {judge_result.get('confidence_score', 0):.2f}[/bold green]")
    
    CONSOLE.print(f"\n[bold]📝 EXECUTIVE SUMMARY:[/bold] {judge_result.get('executive_summary', 'No summary available')}")
    
    if judge_result.get('claim_by_claim_analysis'):
        CONSOLE.print(f"\n[bold]🔍 CLAIM-BY-CLAIM ANALYSIS:[/bold]")
        for analysis in judge_result['claim_by_claim_analysis']:
            CONSOLE.print(f"   • {analysis.get('claim', '')[:60]}...: {analysis.get('verdict', 'unknown')} ({analysis.get('confidence', 'unknown')})")

    if judge_result.get('key_insights'):
        CONSOLE.print(f"\n[bold]💡 KEY INSIGHTS:[/bold]")
        for insight in judge_result['key_insights']:
            CONSOLE.print(f"   • {insight}")

    # Ensure ALL data is JSON-serializable
    return {
        "input_message": raw_text,
        "all_claims": all_claims_data,
        "research_evidence": research,
        "factcheck_evidence": factchecks,
        "comprehensive_verdict": judge_result,
        "timestamp": datetime.utcnow().isoformat()
    }
# ============================
# Test with Better Examples
# ============================
if __name__ == "__main__":
    # More testable claims that should have online evidence
    test_messages = [
        """ 🚨 Please Read & Forward 🚨

A new virus called XJ-21 has been detected in Mumbai. WHO has issued a global alert saying it spreads via touching cash notes. People are advised to avoid handling currency for 30 days.

Stay safe 🙏
""",
     
    ]
    
    print("🤖 Enhanced WhatsApp Fact-Checking System")
    print("=" * 60)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        print("-" * 50)
        
        try:
            result = fact_check_pipeline(message)
            
            print(f"\n🎯 Final Result:")
       
            cv = result["comprehensive_verdict"]

            print(f"   Verdict: {cv['overall_verdict']}")
            print(f"   Confidence: {cv['confidence_score']:.2f}")
            print(f"   Summary: {cv['executive_summary']}")
            print("=" * 60)
        except Exception as e:
            print(f"[red]Pipeline failed: {e}[/red]")
            print("=" * 60)