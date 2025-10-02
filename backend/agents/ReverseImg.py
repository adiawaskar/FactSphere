import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from difflib import SequenceMatcher
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util

# Load environment variables
load_dotenv()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Get your SerpAPI key from https://serpapi.com/dashboard
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not SERPAPI_KEY:
    print("❌ SERPAPI_KEY is missing from environment")
else:
    print("✅ Loaded SERPAPI_KEY:", SERPAPI_KEY[:15] + "...")

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36"
}

def get_page_title(html):
    soup = BeautifulSoup(html, "html.parser")
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"]
    if soup.title:
        return soup.title.string
    return ""


def titles_similar(title1, title2):
    # Semantic similarity
    emb1 = model.encode(title1, convert_to_tensor=True)
    emb2 = model.encode(title2, convert_to_tensor=True)
    semantic_score = util.cos_sim(emb1, emb2).item()  # 0–1

    # Fuzzy similarity (optional, still useful for exact overlaps)
    fuzzy_score = fuzz.token_set_ratio(title1, title2) / 100.0

    # Weighted combination (tweak weights as needed)
    final_score = 0.7 * semantic_score + 0.3 * fuzzy_score
    return final_score

def download_page(url):
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Error downloading page: {e}")
        return None

# def extract_images(html, base_url):
#     soup = BeautifulSoup(html, "html.parser")
#     images = []
#     for img in soup.find_all("img"):
#         src = img.get("src") or img.get("data-src") or img.get("data-lazy")
#         if src:
#             if not src.startswith(('http', '//')):
#                 src = urljoin(base_url, src)
#             elif src.startswith('//'):
#                 src = 'https:' + src
#             if (
#                 "placeholder" in src.lower()
#                 or "sprite" in src.lower()
#                 or "icon" in src.lower()
#                 or "logo" in src.lower()
#                 or "tracker" in src.lower()
#                 or "pixel" in src.lower()
#                 or src.endswith((".svg", ".gif"))
#             ):
#                 continue
#             if src.startswith('http'):
#                 images.append(src)
#     return images[:5]

def extract_images(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Check og:image first (most reliable for news)
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        return [urljoin(base_url, og_img["content"])]

    # 2. Otherwise, find images inside <article> or <figure>
    candidates = []
    for tag in soup.select("article img, figure img"):
        src = tag.get("src") or tag.get("data-src")
        if src and not any(x in src.lower() for x in ["logo", "icon", "sprite", "pixel", "ads"]):
            if src.startswith("//"):
                src = "https:" + src
            if not src.startswith("http"):
                src = urljoin(base_url, src)
            candidates.append(src)
    
    return candidates[:5]  # just pick top 1–2 main images

def true_reverse_image_search(image_url):
    if not SERPAPI_KEY:
        print("❌ Missing SERPAPI_KEY!")
        return []
    try:
        print("🔍 Performing TRUE reverse image search...")
        print(f"📸 Image URL: {image_url}")
        api_url = "https://serpapi.com/search"
        params = {
            'engine': 'google_lens',
            'url': image_url,
            'api_key': SERPAPI_KEY
        }
        print("⏳ Waiting for reverse search results...")
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        results = response.json()
        search_results = []
        if 'visual_matches' in results:
            for match in results['visual_matches']:
                search_results.append({
                    'title': match.get('title', 'No title'),
                    'source': match.get('source', 'Unknown source'),
                    'link': match.get('link', 'No link'),
                    'thumbnail': match.get('thumbnail', '')
                })
        print(f"✅ Found {len(search_results)} visual matches")
        return search_results
    except requests.exceptions.Timeout:
        print("❌ Request timeout - SerpAPI might be slow")
        return []
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("❌ No reverse image search results found")
        elif e.response.status_code == 401:
            print("❌ Invalid SerpAPI key")
        else:
            print(f"❌ HTTP Error: {e}")
        return []
    except Exception as e:
        print(f"❌ Reverse search error: {e}")
        return []

def categorize_source(source_name, link):
    source_lower = source_name.lower()
    if any(x in source_lower for x in ["reuters", "bbc", "times", "week", "cnn", "news", "srn"]):
        return "✅ Credible News"
    elif "twitter" in source_lower or "x.com" in link or "facebook" in source_lower or "instagram" in source_lower:
        return "⚠️ Social Media"
    else:
        return "❓ Other/Unknown"

# def analyze_results(results, original_title):
#     if not results:
#         print("❌ No results to analyze")
#         return
#     print("\n" + "="*60)
#     print("📊 REVERSE IMAGE SEARCH ANALYSIS")
#     print("="*60)
#     sources = set(r['source'] for r in results)
#     print(f"📈 Found matches from {len(sources)} unique sources")
#     print(f"🔍 Total visual matches: {len(results)}")

#     print(f"\n📰 Original Article Title: {original_title}")

#     for i, result in enumerate(results, 1):
#         category = categorize_source(result['source'], result['link'])
#         similar, ratio = titles_similar(original_title, result['title'])
#         print(f"\n--- Match {i} ---")
#         print(f"   🏷️ Title: {result['title']}")
#         print(f"   🌍 Source: {result['source']} ({category})")
#         print(f"   🔗 Link: {result['link']}")
#         print(f"   🔎 Similar to original: {similar} (score={ratio:.2f})")

#     credible_count = sum(1 for r in results if categorize_source(r['source'], r['link']) == "✅ Credible News")
#     if credible_count >= 3:
#         print("\n✅ HIGH CONFIDENCE: Image appears on multiple credible news outlets")
#     elif credible_count >= 1:
#         print("\n⚠️ MEDIUM CONFIDENCE: Image found, but limited credible coverage")
#     else:
#         print("\n❌ LOW CONFIDENCE: No credible news sources found, verify carefully")

def analyze_results(results, original_title, threshold=0.4):
    if not results:
        print("❌ No results to analyze")
        return

    # Compute similarity scores
    scored_results = []
    for r in results:
        ratio = titles_similar(original_title, r['title'])
        scored_results.append({
            "title": r['title'],
            "source": r['source'],
            "link": r['link'],
            "score": ratio,  # already normalized to 0–1
            "category": categorize_source(r['source'], r['link'])
        })

    # Sort by score (descending)
    scored_results.sort(key=lambda x: x['score'], reverse=True)

    # Separate credible vs non-credible
    credible_results = [r for r in scored_results if r['category'] == "✅ Credible News"]

    print(f"\n📰 Original Article Title: {original_title}\n")

    # Check confidence
    if len([r for r in scored_results if r['score'] >= threshold]) >= 3:
        verdict = "✅ Verdict: HIGH CONFIDENCE"
        reason = f"3 credible sources matched with strong similarity"
        top_matches = scored_results[:3]
    else:
        verdict = "❌ Verdict: LOW CONFIDENCE"
        reason = f"No credible sources matched strongly"
        top_matches = scored_results[:3]  # just pick best 3 overall

    # Print verdict
    print(verdict)
    print(f"Reason: {reason}\n")

    # Print matches
    if verdict.startswith("✅"):
        print("Top Matches:")
    else:
        print("Closest Matches:")

    for i, r in enumerate(top_matches, 1):
        print(f"{i}. {r['source']} — \"{r['title']}\" ({r['score']:.2f})")
        print(f"   🔗 {r['link']}")

def verify_news(url):
    print(f"🔍 Verifying news with TRUE reverse image search")
    print(f"📄 Article URL: {url}")
    print("-" * 60)
    html = download_page(url)
    if not html:
        return
    images = extract_images(html, url)
    if not images:
        print("❌ No real images found in article (only placeholders/logos)")
        return
    print(f"📷 Found {len(images)} real image(s)")
    print(images)
    original_title = get_page_title(html)
    for idx, image_url in enumerate(images, 1):
        print(f"\n🖼️ Running reverse search for image {idx}/{len(images)}: {image_url}")
        results = true_reverse_image_search(image_url)
        analyze_results(results, original_title)

def create_env_template():
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write("# Get your FREE API key from: https://serpapi.com\n")
            f.write("SERPAPI_KEY=your_serpapi_key_here\n")
        print(f"📁 Created {env_file} file. Please add your SerpAPI key.")

if __name__ == "__main__":
    create_env_template()
    test_url = "https://www.news18.com/world/israel-tightens-siege-on-gaza-as-hamas-signals-rejection-of-trump-peace-plan-ws-l-9609175.html"
    verify_news(test_url)
