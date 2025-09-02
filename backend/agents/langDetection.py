# import requests
# from bs4 import BeautifulSoup
# from langdetect import detect, DetectorFactory
# import json

# # Make langdetect results consistent
# DetectorFactory.seed = 0  

# SUPPORTED_LANGS = ["en"]  # Add more if needed

# def fetch_article_text(url):
#     try:
#         # Fetch page
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()

#         # Parse HTML
#         soup = BeautifulSoup(response.text, "html.parser")

#         # Extract paragraphs
#         paragraphs = soup.find_all("p")
#         text = " ".join([p.get_text() for p in paragraphs])

#         return text.strip()
#     except Exception as e:
#         return None

# def process_url(url):
#     article_text = fetch_article_text(url)
    
#     if not article_text or len(article_text) < 20:
#         return {
#             "status": "error",
#             "reason": "Could not extract enough text from URL"
#         }

#     try:
#         lang = detect(article_text)
        
#         if lang not in SUPPORTED_LANGS:
#             return {
#                 "status": "rejected",
#                 "lang": lang,
#                 "reason": "unsupported language"
#             }
        
#         return {
#             "status": "accepted",
#             "lang": lang,
#             "text": article_text[:500] + "..."  # show only first 500 chars
#         }
    
#     except Exception as e:
#         return {
#             "status": "error",
#             "reason": str(e)
#         }


# # ----------------------
# # 🔹 Example Usage
# # ----------------------
# url = "https://www.divyabhaskar.co.in/local/gujarat/ahmedabad/news/gujarat-heavy-rain-sabarmati-riverfront-walkway-submerged-135749005.html"  # Example
# result = process_url(url)
# print(json.dumps(result, indent=2))
from langdetect import detect, DetectorFactory
import json

# Make langdetect results consistent
DetectorFactory.seed = 0  

SUPPORTED_LANGS = ["en"]  # Add more if needed

def process_text(article_text):
    if not article_text or len(article_text) < 20:
        return {
            "status": "error",
            "reason": "Not enough text provided"
        }

    try:
        lang = detect(article_text)
        
        if lang not in SUPPORTED_LANGS:
            return {
                "status": "rejected",
                "lang": lang,
                "reason": "unsupported language"
            }
        
        return {
            "status": "accepted",
            "lang": lang,
            "text": article_text[:500] + "..."  # show only first 500 chars
        }
    
    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)
        }


# ----------------------
# 🔹 Example Usage
# ----------------------
# sample_text = "India is one of the fastest-growing economies in the world. It has been strengthening global partnerships and expanding its digital infrastructure."
# result = process_text(sample_text)
# print(json.dumps(result, indent=2))