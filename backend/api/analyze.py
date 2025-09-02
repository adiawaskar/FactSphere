# import os
# import requests
# import tempfile
# import json
# import re
# from urllib.parse import urljoin, urlparse
# from agents.langDetection import process_text
# from agents.susKeywords import analyze_text_for_triggers
# from agents.ImageForensic import analyze_local_images
# from utils.fetch_content import fetch_content

# # Make langdetect deterministic
# SUPPORTED_LANGS = ["en"]

# def analyze_url(url: str, workdir="media_audit"):
#     """
#     Fetch text, images, and videos from a URL, check language, 
#     then run forensic analysis on the images.
#     """
#     # Step 1: Fetch content
#     content = fetch_content(url)
#     text, images, videos = (
#         content.get("text") or "",
#         content.get("images", []),
#         content.get("videos", []),
#     )

#     # Step 2: Language detection
#         # Step 2: Language detection
#     if not text or len(text) < 20:
#         return {"status": "error", "reason": "Insufficient text extracted"}

#     try:
#         lang_result = process_text(text)   # this is a dict
#     except Exception as e:
#         return {"status": "error", "reason": f"Language detection failed: {e}"}

#     if lang_result.get("status") != "accepted":
#         return {"status": "notvalid", "reason": lang_result.get("reason", "Language rejected")}

#     lang = lang_result["lang"]
#     if lang not in SUPPORTED_LANGS:
#         return {"status": "notvalid", "reason": f"Unsupported language: {lang}"}
#     # Step 3: Prepare temp folder for downloaded images
#     tmp_dir = os.path.join(tempfile.gettempdir(), "url_images")
#     os.makedirs(tmp_dir, exist_ok=True)

#     local_image_paths = []
#     for i, img_url in enumerate(images):
#         try:
#             # Resolve relative URLs
#             if not bool(urlparse(img_url).netloc):
#                 img_url = urljoin(url, img_url)

#             resp = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
#             if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
#                 img_path = os.path.join(tmp_dir, f"img_{i}.jpg")
#                 with open(img_path, "wb") as f:
#                     f.write(resp.content)
#                 local_image_paths.append(img_path)
#         except Exception as e:
#             print(f"Failed to download {img_url}: {e}")

#     # Step 4: Run forensic analysis
#     # forensic_report = {}
#     # if local_image_paths:
#     #     forensic_report = analyze_local_images(local_image_paths, workdir)
#     # else:
#     #     forensic_report = {"warning": "No images available for forensic analysis."}

#     # Step 5: Run trigger-word analysis
#     trigger_report = {}
#     try:
#         trigger_report = analyze_text_for_triggers(title, text)
#     except Exception as e:
#         trigger_report = {"error": f"Trigger analysis failed: {e}"}

#     # Step 5: Final report
#     final_report = {
#         "status": "success",
#         "url": url,
#         "lang": lang,
#         "text": text[:500] + ("..." if len(text) > 500 else ""),  # first 500 chars
#         "images": images,
#         "videos": videos,
#         # "forensic_report": forensic_report,
#     }

#     return final_report


# # ---------- Example Usage ----------
# if __name__ == "__main__":
#     test_url = input("Enter a URL: ").strip()
#     report = analyze_url(test_url)
#     print(json.dumps(report, indent=2, ensure_ascii=False))
import os
import requests
import tempfile
import json
from urllib.parse import urljoin, urlparse
from agents.langDetection import process_text
from agents.susKeywords import analyze_text_for_triggers
from agents.ImageForensic import analyze_local_images
from utils.fetch_content import fetch_content

# Make langdetect deterministic
SUPPORTED_LANGS = ["en"]

def analyze_url(url: str, workdir="media_audit"):
    """
    Fetch text, images, and videos from a URL, check language, 
    run trigger analysis and forensic analysis on the images.
    """
    # Step 1: Fetch content
    content = fetch_content(url)
    title, text, images, videos = (
        content.get("title") or "",
        content.get("text") or "",
        content.get("images", []),
        content.get("videos", []),
    )

    # Step 2: Language detection
    if not text or len(text) < 20:
        return {"status": "error", "reason": "Insufficient text extracted"}

    try:
        lang_result = process_text(text)   # this is a dict
    except Exception as e:
        return {"status": "error", "reason": f"Language detection failed: {e}"}

    if lang_result.get("status") != "accepted":
        return {"status": "notvalid", "reason": lang_result.get("reason", "Language rejected")}

    lang = lang_result["lang"]
    if lang not in SUPPORTED_LANGS:
        return {"status": "notvalid", "reason": f"Unsupported language: {lang}"}

    # Step 3: Download images locally for forensic check
    tmp_dir = os.path.join(tempfile.gettempdir(), "url_images")
    os.makedirs(tmp_dir, exist_ok=True)

    local_image_paths = []
    for i, img_url in enumerate(images):
        try:
            # Resolve relative URLs
            if not bool(urlparse(img_url).netloc):
                img_url = urljoin(url, img_url)

            resp = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                img_path = os.path.join(tmp_dir, f"img_{i}.jpg")
                with open(img_path, "wb") as f:
                    f.write(resp.content)
                local_image_paths.append(img_path)
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")

    # Step 4: Run forensic analysis (optional)
    # forensic_report = {}
    # if local_image_paths:
    #     try:
    #         forensic_report = analyze_local_images(local_image_paths, workdir)
    #     except Exception as e:
    #         forensic_report = {"error": f"Forensic analysis failed: {e}"}
    # else:
    #     forensic_report = {"warning": "No images available for forensic analysis."}

    # Step 5: Run trigger-word analysis
    trigger_report = {}
    try:
        trigger_report = analyze_text_for_triggers(title, text)
    except Exception as e:
        trigger_report = {"error": f"Trigger analysis failed: {e}"}
        
    # Step 6: Final report
    final_report = {
        "status": "success",
        "url": url,
        "lang": lang,
        "title": title,
        "text": text[:500] + ("..." if len(text) > 500 else ""),  # preview
        "images": images,
        "videos": videos,
        # "forensic_report": forensic_report,
        "trigger_report": trigger_report,
    }

    return final_report


# ---------- Example Usage ----------
if __name__ == "__main__":
    test_url = "https://www.indiatoday.in/world/us-news/story/trump-aide-peter-navarros-another-bizarre-take-on-india-russia-oil-ties-brahmins-profiteering-2779779-2025-09-01"
    report = analyze_url(test_url)
    print(json.dumps(report, indent=2, ensure_ascii=False))