
# import os
# import requests
# import tempfile
# import json
# from urllib.parse import urljoin, urlparse
# from fastapi import APIRouter, FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Dict, Any

# # ---- Local imports ----
# from backend.agents.langDetection import process_text
# from backend.agents.susKeywords import analyze_text_for_triggers
# # from agents.ImageForensic import analyze_local_images   # optional
# from backend.utils.fetch_content import fetch_content
# from backend.agents.Source_credibility_keshav import publication_reputation_check

# # Make langdetect deterministic
# SUPPORTED_LANGS = ["en"]

# # ---------------- ANALYSIS PIPELINE ----------------
# def analyze(url: str, workdir="media_audit"):
#     """
#     Fetch text, images, and videos from a URL, check language, 
#     run trigger analysis and credibility analysis.
#     """
#     # Step 1: Fetch content
#     # content = fetch_content(url)
#     title, text, images, videos = (
#         content.get("title") or "",
#         content.get("text") or "",
#         content.get("images", []),
#         content.get("videos", []),
#     )

#     # Step 2: Language detection
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

#     # Step 3: Download images locally (optional)
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

#     # Step 4: Trigger-word analysis
#     trigger_report = {}
#     try:
#         trigger_report = analyze_text_for_triggers(title, text)
#     except Exception as e:
#         trigger_report = {"error": f"Trigger analysis failed: {e}"}

#     # Step 5: Source credibility
#     credibility_report = {}
#     try:
#         credibility_report = publication_reputation_check(url, verbose=False)
#     except Exception as e:
#         credibility_report = {"error": f"Credibility check failed: {e}"}
        
#     # Step 6: Final report
#     final_report = {
#         "status": "success",
#         "url": url,
#         "lang": lang,
#         "title": title,
#         "text": text[:500] + ("..." if len(text) > 500 else ""),  # preview
#         "images": images,
#         "videos": videos,
#         # "forensic_report": forensic_report,   # optional
#         "trigger_report": trigger_report,
#         "source_crebility": credibility_report
#     }

#     return final_report

# # ---------------- FASTAPI ROUTER ----------------
# router = APIRouter()

# class AnalyzeRequest(BaseModel):
#     url: str

# @router.post("/analyze")
# async def analyze_endpoint(request: AnalyzeRequest) -> Dict[str, Any]:
#     """
#     API endpoint to analyze a given URL.
#     """
#     try:
#         content=""
#         if request.type=="url" and request.input:
#             content=fetch_content(request.input)
#         if request.type=="text" and request.input:
#             content=request.input
        

#         report = analyze(content, request.url if request.type=="url" else None)

#         if report.get("status") != "success":
#             raise HTTPException(status_code=400, detail=report)

#         return {
#             "success": True,
#             "report": report
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error analyzing URL: {str(e)}")


# # ---------------- RUN DIRECTLY ----------------
# if __name__ == "__main__":
#     # Run as script
#     test_url = "https://www.indiatoday.in/world/us-news/story/trump-aide-peter-navarros-another-bizarre-take-on-india-russia-oil-ties-brahmins-profiteering-2779779-2025-09-01"
#     report = analyze_url(test_url)
#     print(json.dumps(report, indent=2, ensure_ascii=False))

#     # Run API if needed
#     import uvicorn
#     app = FastAPI(title="Media Audit API")
#     app.include_router(router)
#     uvicorn.run(app, host="0.0.0.0", port=8000)
import os
import requests
import tempfile
import json
from urllib.parse import urljoin, urlparse
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# ---- Local imports ----
from backend.agents.langDetection import process_text
from backend.agents.susKeywords import analyze_text_for_triggers
from backend.utils.fetch_content import fetch_content
from backend.agents.Source_credibility_keshav import publication_reputation_check

# Supported languages
SUPPORTED_LANGS = ["en"]

# -------------------- COMMON PIPELINE --------------------
def run_pipeline(text: str, url: str = None, title: str = "", images=None, videos=None):
    if not images:
        images = []
    if not videos:
        videos = []

    # Step 1: Language detection
    if not text or len(text) < 20:
        return {"status": "error", "reason": "Insufficient text extracted"}

    try:
        lang_result = process_text(text)   # dict
    except Exception as e:
        return {"status": "error", "reason": f"Language detection failed: {e}"}

    if lang_result.get("status") != "accepted":
        return {"status": "notvalid", "reason": lang_result.get("reason", "Language rejected")}

    lang = lang_result["lang"]
    if lang not in SUPPORTED_LANGS:
        return {"status": "notvalid", "reason": f"Unsupported language: {lang}"}

    # Step 2: Download images locally (optional)
    tmp_dir = os.path.join(tempfile.gettempdir(), "url_images")
    os.makedirs(tmp_dir, exist_ok=True)

    local_image_paths = []
    for i, img_url in enumerate(images):
        try:
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

    # Step 3: Trigger analysis
    trigger_report = {}
    try:
        trigger_report = analyze_text_for_triggers(title, text)
    except Exception as e:
        trigger_report = {"error": f"Trigger analysis failed: {e}"}

    # Step 4: Source credibility
    credibility_report = {}
    try:
        if url:
            credibility_report = publication_reputation_check(url)
    except Exception as e:
        credibility_report = {"error": f"Credibility check failed: {e}"}

    # Step 5: Final report
    final_report = {
        "status": "success",
        "url": url,
        "lang": lang,
        "title": title,
        "text": text[:1500] + ("..." if len(text) > 1500 else ""),
        "images": images,
        "videos": videos,
        "trigger_report": trigger_report,
        "source_credibility": credibility_report
    }

    return final_report

# -------------------- ANALYZE FUNCTIONS --------------------
def analyze_url(url: str):
    content = fetch_content(url)
    title, text, images, videos = (
        content.get("title") or "",
        content.get("text") or "",
        content.get("images", []),
        content.get("videos", []),
    )
    return run_pipeline(text, url=url, title=title, images=images, videos=videos)


def analyze_text(text: str):
    return run_pipeline(text, url=None, title="User Provided Text", images=[], videos=[])


# -------------------- FASTAPI ROUTER --------------------
router = APIRouter()

class AnalyzeRequest(BaseModel):
    input: str
    type: str   # "url" or "text"

@router.post("/analyze")
async def analyze_endpoint(request: AnalyzeRequest) -> Dict[str, Any]:
    try:
        if request.type == "url":
            report = analyze_url(request.input)
        elif request.type == "text":
            report = analyze_text(request.input)
        else:
            raise HTTPException(status_code=400, detail="Invalid type. Must be 'url' or 'text'.")

        if report.get("status") != "success":
            raise HTTPException(status_code=400, detail=report)

        return {"success": True, "report": report}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing input: {str(e)}")


# -------------------- RUN DIRECTLY --------------------
if __name__ == "__main__":
    test_url = "https://www.indiatoday.in/world/us-news/story/trump-aide-peter-navarros-another-bizarre-take-on-india-russia-oil-ties-brahmins-profiteering-2779779-2025-09-01"
    report = analyze_url(test_url)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Run API if needed
    import uvicorn
    app = FastAPI(title="Media Audit API")
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8000)