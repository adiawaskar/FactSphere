# backend/utils/fetch_content.py
import requests
from bs4 import BeautifulSoup
import html
import re
import urllib.parse
import typing as T

def fetch_content(url: str) -> T.Dict[str, T.List[str]]:
    """Fetch text, images, and videos from a URL."""
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return {"error": str(e), "text": "", "images": [], "videos": []}

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    # --- TEXT ---
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

    # --- IMAGES ---
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            images.append(urllib.parse.urljoin(url, src))

    # --- VIDEOS ---
    videos = []
    # direct <video> tags
    for vid in soup.find_all("video"):
        src = vid.get("src")
        if not src:
            sources = vid.find_all("source")
            if sources:
                src = sources[0].get("src")
        if src:
            videos.append(urllib.parse.urljoin(url, src))

    # embedded <iframe> (like YouTube)
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src")
        if src and any(x in src for x in ["youtube.com", "vimeo.com"]):
            videos.append(src)

    return {"title": title, "text": text, "images": images, "videos": videos}

if __name__ == "__main__":
    url = input("Enter a URL: ").strip()
    content = fetch_content(url)

    print(content)
