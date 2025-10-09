# # backend/utils/fetch_content.py
# import requests
# from bs4 import BeautifulSoup
# import html
# import re
# import urllib.parse
# import typing as T

# def fetch_content(url: str) -> T.Dict[str, T.List[str]]:
#     """Fetch text, images, and videos from a URL."""
#     try:
#         resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
#         resp.raise_for_status()
#     except Exception as e:
#         return {"error": str(e), "text": "", "images": [], "videos": []}

#     soup = BeautifulSoup(resp.text, "html.parser")
#     for tag in soup(["script", "style", "noscript", "iframe"]):
#         tag.decompose()

#     # --- TEXT ---
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

#     # --- IMAGES ---
#     images = []
#     for img in soup.find_all("img"):
#         src = img.get("src") or img.get("data-src")
#         if src:
#             images.append(urllib.parse.urljoin(url, src))

#     # --- VIDEOS ---
#     videos = []
#     # direct <video> tags
#     for vid in soup.find_all("video"):
#         src = vid.get("src")
#         if not src:
#             sources = vid.find_all("source")
#             if sources:
#                 src = sources[0].get("src")
#         if src:
#             videos.append(urllib.parse.urljoin(url, src))

#     # embedded <iframe> (like YouTube)
#     for iframe in soup.find_all("iframe"):
#         src = iframe.get("src")
#         if src and any(x in src for x in ["youtube.com", "vimeo.com"]):
#             videos.append(src)

#     return {"title": title, "text": text, "images": images, "videos": videos}

# if __name__ == "__main__":
#     url = input("Enter a URL: ").strip()
#     content = fetch_content(url)

#     print(content)
# # backend/utils/fetch_content.py
import requests
from bs4 import BeautifulSoup
import html
import re
import urllib.parse
import typing as T

def fetch_content(url: str) -> T.Dict[str, T.Any]:
    """Fetch cleaned article content (title, text, images, videos) from a URL."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CleanBot/1.0)"},
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        return {"error": str(e), "title": "", "text": "", "images": [], "videos": []}

    soup = BeautifulSoup(resp.text, "html.parser")

    # remove unwanted sections
    for tag in soup(["script", "style", "noscript", "iframe", "footer", "header", "form", "nav", "aside"]):
        tag.decompose()

    # --- Extract title ---
    title = (soup.title.string or "").strip() if soup.title else ""

    # --- Find main content block ---
    candidates = soup.find_all(["article", "main", "section", "div"], recursive=True)
    main_block = None
    max_text_len = 0

    for c in candidates:
        text_len = len(c.get_text(" ", strip=True))
        if text_len > max_text_len:
            main_block = c
            max_text_len = text_len

    if main_block:
        text_parts = main_block.find_all(["p", "li"])
        text = "\n".join(t.get_text(" ", strip=True) for t in text_parts)
    else:
        # fallback
        ps = soup.find_all("p")
        text = "\n".join(p.get_text(" ", strip=True) for p in ps)

    text = html.unescape(text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text).strip()

    # --- IMAGES ---
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if src and not src.startswith("data:"):
            abs_url = urllib.parse.urljoin(url, src)
            if abs_url not in images:
                images.append(abs_url)

    # --- VIDEOS ---
    videos = []
    for vid in soup.find_all("video"):
        src = vid.get("src")
        if not src:
            sources = vid.find_all("source")
            if sources:
                src = sources[0].get("src")
        if src:
            abs_url = urllib.parse.urljoin(url, src)
            if abs_url not in videos:
                videos.append(abs_url)

    # YouTube / Vimeo embeds
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src")
        if src and any(x in src for x in ["youtube.com", "youtu.be", "vimeo.com"]):
            if src not in videos:
                videos.append(src)

    return {
        "title": title,
        "text": text,
        "images": images,
        "videos": videos,
    }

if __name__ == "__main__":
    url = input("Enter a URL: ").strip()
    content = fetch_content(url)
    print("\n=== TITLE ===")
    print(content["title"])
    print("\n=== TEXT ===")
    print(content["text"][:2000])  # limit for readability
    print("\n=== IMAGES ===")
    print("\n".join(content["images"]))
    print("\n=== VIDEOS ===")
    print("\n".join(content["videos"]))