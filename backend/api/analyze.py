
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
from backend.agents.ReverseImg import verify_news
from backend.agents.fake_news_detection.analyze_url import cross_verify_news

# Supported languages
SUPPORTED_LANGS = ["en"]

def calculate_final_verdict(report_data):
    """
    Calculate final risk assessment and verdict based on all analysis components
    """
    
    # Initialize scores
    scores = {
        'source_credibility': 0,
        'content_risk': 0,
        'verification_confidence': 0,
        'image_consistency': 0
    }
    
    weights = {
        'source_credibility': 0.4,
        'content_risk': 0.25, 
        'verification_confidence': 0.2,
        'image_consistency': 0.15
    }
    
    # 1. Source Credibility Score (0-1, higher is better)
    if 'source_credibility' in report_data:
        cred = report_data['source_credibility']
        scores['source_credibility'] = cred.get('score', 0)
    
    # 2. Content Risk Score (0-1, higher is worse)
    if 'trigger_report' in report_data:
        trigger = report_data['trigger_report']
        # total_requested = trigger.get('trigger_count_requested', 60)
        total_found = trigger.get('trigger_count_received', 0)
        if total_found == 0:
            scores['content_risk'] = 0.1  # Low risk - no concerning phrases
        elif total_found <3:
            scores['content_risk'] = 0.3  # Medium risk - one concerning phrase
        elif total_found <10:
            scores['content_risk'] = 0.4  # High risk - multiple concerning phrases
        else:  # 3+ phrases
            scores['content_risk'] = 0.6  # Very high risk - many concerning phrases
        
    # 3. Verification Confidence (0-1, higher is better)
    if 'cross_verify' in report_data:
        cross = report_data['cross_verify']
        verification = cross.get('verification', {})
        consensus = cross.get('consensus_analysis', {})
        
        # Base confidence from verification
        base_confidence = verification.get('confidence', 0)
        confirmations=consensus.get('confirmations',[]),
        # Boost from consensus and credible sources
        consensus_score = consensus.get('consensus_score', 0)
        credible_sources = len(confirmations)
        total_sources = consensus.get('unique_sources', 1)
        
        credible_ratio = credible_sources / total_sources if total_sources > 0 else 0
        print(credible_sources,total_sources)
        print(base_confidence,consensus_score+credible_ratio)
        # Combined verification score
        scores['verification_confidence'] = min(
            consensus_score, 1.0
        )
    

    if 'reverse_img' in report_data and report_data['reverse_img'].get('status') == 'success':
        image_results = report_data['reverse_img'].get('image_results', [])
        
        if image_results:
            total_score = 0
            image_count = 0
            
            for image_data in image_results:
                best_matches = image_data.get('best_matches', [])
                if best_matches:
                    # Take the best match for this image
                    best_match = best_matches[0]
                    match_score = best_match.get('score', 0)
                    source_category = best_match.get('category', '')
                    
                    # Apply credibility boost
                    credibility_boost = 0.3 if 'Credible News' in source_category else 0.2
                    image_score = min(match_score + credibility_boost, 1.0)
                    
                    total_score += image_score
                    image_count += 1
            
            # Average across all images
            if image_count > 0:
                scores['image_consistency'] = (total_score / image_count)
            else:
                scores['image_consistency'] = 0.0

    # Calculate weighted final score (0-1, higher is more credible)
    final_score = 0
    for key, score in scores.items():
        print(weights[key],score)
        final_score += score * weights[key]
    
    # Convert to risk score (0-1, higher is more risky)
    risk_score = (
    (1 - scores['source_credibility']) * weights['source_credibility'] +
    scores['content_risk'] * weights['content_risk'] +
    (1 - scores['verification_confidence']) * weights['verification_confidence'] +
    (1 - scores['image_consistency']) * weights['image_consistency']
)
    
    # Generate verdict and statement
    verdict, statement = generate_verdict_statement(
        risk_score, 
        scores, 
        report_data
    )
    
    return {
        'risk_score': risk_score,
        'final_verdict': verdict,
        'statement': statement,
        'breakdown': {
            'source_credibility_score': scores['source_credibility'],
            'content_risk_score': scores['content_risk'],
            'verification_confidence': scores['verification_confidence'],
            'image_consistency_score': scores['image_consistency'],
            'final_credibility_score': final_score
        }
    }


def generate_verdict_statement(risk_score, scores, report_data):
    """
    Generate human-readable verdict and explanation
    """
    
    # Determine risk level
    if risk_score < 0.3:
        risk_level = "LOW RISK"
        emoji = "✅"
    elif risk_score < 0.6:
        risk_level = "MEDIUM RISK" 
        emoji = "⚠️"
    else:
        risk_level = "HIGH RISK"
        emoji = "🚨"
    
    # Build statement components
    components = []
    
    # Source analysis
    source_score = scores['source_credibility']
    if source_score >= 0.8:
        components.append("highly credible source")
    elif source_score >= 0.6:
        components.append("moderately credible source") 
    else:
        components.append("source credibility concerns")
    
    # Content analysis
    content_risk = scores['content_risk']
    if content_risk > 0.5:
        components.append("multiple concerning phrases detected")
    elif content_risk > 0.2:
        components.append("some flagged content present")
    else:
        components.append("minimal content concerns")
    
    # Verification analysis
    verification_score = scores['verification_confidence']
    if verification_score >= 0.7:
        components.append("strong cross-verification")
    elif verification_score >= 0.4:
        components.append("moderate verification support")
    else:
        components.append("limited independent verification")
    
    # Image analysis
    if scores['image_consistency'] > 0:
        if scores['image_consistency'] >= 0.7:
            components.append("images verified across credible sources")
        else:
            components.append("images show partial verification")
    
    # Generate final statement
    statement = f"{emoji} {risk_level} - This content shows {risk_level.lower()} due to "
    statement += ", ".join(components[:-1]) + f" and {components[-1]}."
    
    # Add specific recommendations based on risk level
    if risk_score < 0.3:
        statement += " The information appears generally reliable with standard verification recommended for critical claims."
    elif risk_score < 0.6:
        statement += " Additional verification with authoritative sources is recommended before sharing or acting on this information."
    else:
        statement += " Extensive independent verification is strongly recommended as this content shows significant credibility concerns."
    
    verdict = f"{emoji} {risk_level}"
    
    return verdict, statement


# Example usage with your data:
def create_final_risk_assessment(report_data):
    """
    Main function to create comprehensive risk assessment
    """
    verdict_data = calculate_final_verdict(report_data)
    
    # Add additional context from the report
    additional_info = {
        'flagged_phrases_count': len(report_data.get('trigger_report', {}).get('list_of_phrases', [])),
        'cross_verification_sources': report_data.get('cross_verify', {}).get('consensus_analysis', {}).get('total_sources', 0),
        'image_verification_status': report_data.get('reverse_img', {}).get('status', 'not_available'),
        'primary_source': report_data.get('source_credibility', {}).get('domain', 'unknown')
    }
    
    return {
        **verdict_data,
        'additional_context': additional_info
    }

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
    
    #Step 6:reverse image search
    img_report={}
    try:
        if url:
            img_report=verify_news(url)
    except Exception as e:
        img_report = {"error": f"Reverse Image search check failed: {e}"}
    
    #Step 7:fadt cross verify
    cross_verify={}
    try:
        if url:
            cross_verify=cross_verify_news(url)
    except Exception as e:
        cross_verify = {"error": f"Reverse Image search check failed: {e}"}


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
        "source_credibility": credibility_report,
        "reverse_img":img_report,
        "cross_verify":cross_verify
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
        
        final_risk_assessment = create_final_risk_assessment(report)
        
        # Include it in the response
        report["final_risk_assessment"] = final_risk_assessment

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