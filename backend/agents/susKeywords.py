
# # """
# # Dynamic trigger-word scanner (LLM-driven, no hard-coded list)
# # """

# # import os
# # import sys
# # import re
# # import json
# # import html
# # from rapidfuzz import fuzz, process

# # import typing as T
# # import requests
# # from bs4 import BeautifulSoup
# # from dotenv import load_dotenv
# # from groq import Groq

# # BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# # ENV_PATH = os.path.join(BASE_DIR, ".env")
# # load_dotenv(ENV_PATH)

# # def safe_json(raw: str) -> dict:
# #     """Robust JSON parsing from LLM output"""
# #     if not raw:
# #         return {"triggers": []}
    
# #     # Clean the output first
# #     cleaned = raw.strip()
    
# #     # Remove markdown code blocks if present
# #     cleaned = re.sub(r'```json\s*', '', cleaned)
# #     cleaned = re.sub(r'```\s*', '', cleaned)
    
# #     try:
# #         return json.loads(cleaned)
# #     except json.JSONDecodeError:
# #         print("⚠️ JSON parse failed, trying to extract objects...")
        
# #         # Try to find JSON objects with "phrase" key
# #         objects = re.findall(r'\{[^{}]*"phrase"[^{}]*\}', cleaned, re.DOTALL)
# #         triggers = []
# #         for obj in objects:
# #             try:
# #                 # Clean up the object string
# #                 obj_clean = re.sub(r',\s*}', '}', obj)  # Fix trailing commas
# #                 triggers.append(json.loads(obj_clean))
# #             except Exception as e:
# #                 print(f"❌ Failed to parse object: {e}")
# #                 continue
        
# #         if triggers:
# #             print(f"✅ Salvaged {len(triggers)} trigger objects")
# #             return {"triggers": triggers}
        
# #         # Last resort: try to extract just phrases
# #         phrases = re.findall(r'"phrase"\s*:\s*"([^"]+)"', cleaned)
# #         if phrases:
# #             print(f"✅ Extracted {len(phrases)} raw phrases")
# #             return {"triggers": [{"phrase": p} for p in phrases]}
        
# #         return {"triggers": []}

# # class LLMClient:
# #     def __init__(self, api_key: str = None, model: str = None):
# #         api_key = api_key or os.getenv("GROQ_API_KEY")
# #         if not api_key:
# #             raise RuntimeError("GROQ_API_KEY not set")
        
# #         print("✅ Initializing Groq Client...")
# #         self.client = Groq(api_key=api_key)
# #         self.model = model or os.getenv("MISINFO_MODEL", "llama-3.1-8b-instant")
# #         print(f"✅ Using model: {self.model}")

# #     def get_dynamic_triggers(self, article_title: str, article_text: str, max_triggers: int = 60) -> dict:
# #         """Get trigger phrases from LLM with better prompting"""
        
# #         # Prepare text (limit size to avoid token limits)
# #         clean_text = article_text.replace('"', "'").replace('\n', ' ').strip()
# #         text_preview = clean_text[:3000]  # Limit text to avoid token overflow
        
# #         system_msg = """You are a misinformation detection expert. Extract EXACT phrases from the article that indicate potential misinformation, sensationalism, or manipulative language. Return ONLY valid JSON."""

# #         user_prompt = f"""
# # EXTRACT misleading or sensational phrases from this article. Return ONLY JSON.

# # CRITICAL: Only extract phrases that appear VERBATIM in the text below.

# # ARTICLE TITLE: {article_title}
# # ARTICLE TEXT: {text_preview}

# # OUTPUT FORMAT (JSON only):
# # {{
# #   "triggers": [
# #     {{
# #       "phrase": "exact phrase from text",
# #       "category": "sensationalism/conspiracy/misleading"
# #     }}
# #   ]
# # }}

# # Rules:
# # - Extract 5-15 strongest phrases
# # - Phrases must be 5+ words long
# # - Must be exact matches from the text
# # - No commentary, only JSON
# # """

# #         try:
# #             print("🔹 Sending request to LLM...")
# #             completion = self.client.chat.completions.create(
# #                 model=self.model,
# #                 messages=[
# #                     {"role": "system", "content": system_msg},
# #                     {"role": "user", "content": user_prompt},
# #                 ],
# #                 temperature=0.1,  # Lower temperature for more consistent JSON
# #                 max_tokens=1000,
# #             )

# #             response = completion.choices[0].message.content.strip()
# #             print("----- RAW LLM OUTPUT -----")
# #             print(response)
# #             print("----- END OUTPUT -----")

# #             return safe_json(response)
            
# #         except Exception as e:
# #             print(f"❌ LLM request failed: {e}")
# #             return {"triggers": []}

# # def find_phrase_in_text(phrase: str, text: str) -> str:
# #     """Find the best match for a phrase in text and return context snippet"""
# #     if not phrase or not text:
# #         return ""
    
# #     # Try exact match first
# #     phrase_lower = phrase.lower()
# #     text_lower = text.lower()
    
# #     idx = text_lower.find(phrase_lower)
# #     if idx != -1:
# #         start = max(0, idx - 80)
# #         end = min(len(text), idx + len(phrase) + 80)
# #         snippet = text[start:end].replace("\n", " ").strip()
# #         return f"...{snippet}..."
    
# #     # Try fuzzy match if exact fails
# #     words = phrase.split()
# #     if len(words) >= 3:
# #         # Search for partial matches of key parts
# #         for i in range(0, len(words) - 2):
# #             subphrase = " ".join(words[i:i+3])
# #             idx = text_lower.find(subphrase.lower())
# #             if idx != -1:
# #                 start = max(0, idx - 100)
# #                 end = min(len(text), idx + len(subphrase) + 100)
# #                 snippet = text[start:end].replace("\n", " ").strip()
# #                 return f"...{snippet}..."
    
# #     return ""

# # def deduplicate_phrases(phrases: list) -> list:
# #     """Remove duplicate and overlapping phrases"""
# #     unique_phrases = []
    
# #     for phrase_data in sorted(phrases, key=lambda x: len(x.get("phrase", "")), reverse=True):
# #         current_phrase = phrase_data.get("phrase", "").lower()
        
# #         # Check if this phrase is contained in any already added phrase
# #         is_duplicate = False
# #         for existing in unique_phrases:
# #             existing_phrase = existing.get("phrase", "").lower()
# #             if (current_phrase in existing_phrase or 
# #                 existing_phrase in current_phrase or
# #                 fuzz.ratio(current_phrase, existing_phrase) > 80):
# #                 is_duplicate = True
# #                 break
        
# #         if not is_duplicate and current_phrase:
# #             unique_phrases.append(phrase_data)
    
# #     return unique_phrases

# # def analyze_text_for_triggers(title: str, text: str) -> dict:
# #     """
# #     Run the dynamic trigger-word scanner on article text
# #     """
# #     client = LLMClient()
# #     max_triggers_hint = int(os.getenv("MAX_TRIGGERS", "60"))

# #     # Get dynamic triggers from LLM
# #     print("🔄 Getting triggers from LLM...")
# #     triggers_obj = client.get_dynamic_triggers(title, text, max_triggers=max_triggers_hint)
# #     raw_triggers = triggers_obj.get("triggers", [])
    
# #     print(f"📊 Raw triggers from LLM: {len(raw_triggers)}")
    
# #     # Filter for valid phrases and find snippets
# #     results = []
# #     for trigger in raw_triggers:
# #         phrase = trigger.get("phrase", "").strip()
# #         if len(phrase.split()) >= 5:  # At least 5 words
# #             snippet = find_phrase_in_text(phrase, text)
# #             if snippet:  # Only keep if we found it in text
# #                 results.append({
# #                     "phrase": phrase,
# #                     "snippet": snippet
# #                 })
    
# #     # Deduplicate and limit to top 10
# #     unique_results = deduplicate_phrases(results)
# #     final_results = unique_results[:10]
    
# #     print(f"🎯 Final triggers found: {len(final_results)}")
    
# #     return {
# #         "title": title,
# #         "model": client.model,
# #         "trigger_count_requested": max_triggers_hint,
# #         "trigger_count_received": len(raw_triggers),
# #         "list_of_phrases": final_results,
# #     }

# # def main(url: str):
# #     """Test function - fetch content and analyze"""
# #     try:
# #         # Simple content fetch (you might want to use your existing fetch_content function)
# #         response = requests.get(url, timeout=15)
# #         soup = BeautifulSoup(response.text, 'html.parser')
        
# #         title = soup.title.string if soup.title else "No title"
        
# #         # Remove scripts and styles
# #         for script in soup(["script", "style"]):
# #             script.decompose()
            
# #         text = soup.get_text()
# #         text = re.sub(r'\s+', ' ', text).strip()
        
# #         print(f"📄 Analyzing: {title}")
# #         print(f"📝 Text length: {len(text)} chars")
        
# #         result = analyze_text_for_triggers(title, text)
        
# #         print("\n🎯 RESULTS:")
# #         print(json.dumps(result, indent=2))
        
# #     except Exception as e:
# #         print(f"❌ Error: {e}")

# # if __name__ == "__main__":
# #     if len(sys.argv) != 2:
# #         print("Usage: python scan_triggers.py <url>")
# #         sys.exit(1)
# #     main(sys.argv[1])
# """
# Dynamic trigger-word scanner (LLM-driven) - Returns Top 3 Phrases
# """

# import os
# import sys
# import re
# import json
# from rapidfuzz import fuzz, process
# from groq import Groq
# from dotenv import load_dotenv

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# ENV_PATH = os.path.join(BASE_DIR, ".env")
# load_dotenv(ENV_PATH)

# def safe_json(raw: str) -> dict:
#     """Robust JSON parsing from LLM output"""
#     if not raw:
#         return {"triggers": []}
    
#     cleaned = raw.strip()
#     cleaned = re.sub(r'```json\s*', '', cleaned)
#     cleaned = re.sub(r'```\s*', '', cleaned)
    
#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         print("⚠️ JSON parse failed, extracting phrases...")
        
#         # Extract phrases using regex
#         phrases = re.findall(r'"phrase"\s*:\s*"([^"]+)"', cleaned)
#         if phrases:
#             print(f"✅ Extracted {len(phrases)} phrases")
#             return {"triggers": [{"phrase": p} for p in phrases]}
        
#         return {"triggers": []}

# class LLMClient:
#     def __init__(self):
#         api_key = os.getenv("GROQ_API_KEY")
#         if not api_key:
#             raise RuntimeError("GROQ_API_KEY not set")
        
#         self.client = Groq(api_key=api_key)
#         self.model = os.getenv("MISINFO_MODEL", "llama-3.1-8b-instant")

#     def get_dynamic_triggers(self, article_title: str, article_text: str) -> dict:
#         """Get trigger phrases from LLM - focused on top 3"""
        
#         # Limit text to avoid token overflow
#         text_preview = article_text[:2500].replace('"', "'").replace('\n', ' ').strip()

#         user_prompt = f"""
# Identify ANY genuinely concerning phrases in this article that show clear misinformation, 
# conspiracy theories, or heavy sensationalism. Return ONLY phrases that are clearly problematic. Return ONLY JSON.

# ARTICLE TITLE: {article_title}
# ARTICLE TEXT: {text_preview}

# CRITICAL RULES:

# - Phrases must appear VERBATIM in the text above
# - Choose phrases that are most sensational, misleading, or manipulative
# - Each phrase should be 5+ words long
# - Return ONLY this JSON format, no other text:

# {{
#   "triggers": [
#     {{"phrase": "exact phrase 1 from text"}},
#     {{"phrase": "exact phrase 2 from text"}}, 
#     ...and other phrases
#     // Can be empty if no concerning phrases!
#   ]
# }}
# """

#         try:
#             completion = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=[{"role": "user", "content": user_prompt}],
#                 temperature=0.1,
#                 max_tokens=500,
#             )

#             response = completion.choices[0].message.content.strip()
#             print("----- LLM OUTPUT -----")
#             print(response)
#             return safe_json(response)
            
#         except Exception as e:
#             print(f"❌ LLM request failed: {e}")
#             return {"triggers": []}

# def find_phrase_snippet(phrase: str, text: str) -> str:
#     """Find phrase in text and return context snippet"""
#     if not phrase or not text:
#         return ""
    
#     phrase_lower = phrase.lower()
#     text_lower = text.lower()
    
#     # Exact match
#     idx = text_lower.find(phrase_lower)
#     if idx != -1:
#         start = max(0, idx - 60)
#         end = min(len(text), idx + len(phrase) + 60)
#         snippet = text[start:end].replace("\n", " ").strip()
#         return f"...{snippet}..."
    
#     return ""

# def select_top_phrases(triggers: list, text: str) -> list:
#     """Select and validate top 3 phrases"""
#     valid_phrases = []
    
#     for trigger in triggers:
#         phrase = trigger.get("phrase", "").strip()
#         # Must be at least 4 words and found in text
#         if len(phrase.split()) >= 4:
#             snippet = find_phrase_snippet(phrase, text)
#             if snippet:
#                 valid_phrases.append({
#                     "phrase": phrase,
#                     "snippet": snippet
#                 })
    
#     # Return top 3 valid phrases (or fewer if not enough found)
#     return valid_phrases[:3]

# def analyze_text_for_triggers(title: str, text: str) -> dict:
#     """
#     Analyze text and return exactly 3 best trigger phrases
#     """
#     client = LLMClient()

#     # Get triggers from LLM
#     print("🔄 Getting top 3 triggers from LLM...")
#     triggers_obj = client.get_dynamic_triggers(title, text)
#     raw_triggers = triggers_obj.get("triggers", [])
    
#     print(f"📊 Raw triggers from LLM: {len(raw_triggers)}")
    
#     # Select top 3 valid phrases
#     final_phrases = select_top_phrases(raw_triggers, text)
    
#     print(f"🎯 Final top phrases: {len(final_phrases)}")
    
#     return {
#         "title": title,
#         "model": client.model,
#         "trigger_count_requested": 3,
#         "trigger_count_received": len(raw_triggers),
#         "list_of_phrases": final_phrases,
#     }

# # Simple test
# if __name__ == "__main__":
#     # Test with sample text
#     test_title = "Will Vijay be arrested for Karur stampede? Tamil Nadu Minister responds"
#     test_text = """
#     Two-thirds of Syria’s new parliament will be chosen by electoral colleges, with the rest appointed by interim President Ahmed al-Sharaa.



# 02:06
# Syria set for first parliamentary elections since the fall of the Assad regime


# By Tim Hume and News Agencies

# Published On 5 Oct 2025
# 5 Oct 2025
# Click here to share on social media
# Share

# Save

# Syria is holding parliamentary elections for the first time since the overthrow of longtime ruler Bashar al-Assad, a landmark moment in the country’s fragile transition after nearly 14 years of war.

# Members of Syria’s electoral colleges gathered on Sunday to vote for the new lawmakers in a process being criticised as undemocratic, with a third of the 210 members of the revamped People’s Assembly appointed by interim leader, Ahmed al-Sharaa.

# Recommended Stories
# list of 4 items
# list 1 of 4In his first UN speech, Syria’s al-Sharaa urges end to all sanctions
# list 2 of 4Syrian President al-Sharaa sits down with US general who arrested him
# list 3 of 4Ukraine, Syria restore diplomatic ties after breakdown during Assad regime
# list 4 of 4Ahmed al-Sharaa’s high-stakes bid to remake Syria
# end of list
# The remaining representatives will not be voted on directly by the people, but chosen instead by electoral colleges around the country.

# Critics say the system favours well-connected figures and is likely to keep power concentrated in the hands of Syria’s new rulers, rather than paving the way for genuine democratic change.

# Syrian President Ahmed al-Sharaa
# Interim President Ahmed al-Sharaa will directly appoint one-third of the deputies [File: Stephanie Lecocq/AFP]
# In a joint statement last month, more than a dozen nongovernmental organisations said the process means al-Sharaa “can effectively shape a parliamentary majority composed of individuals he selected or ensured loyalty from”, which risked “undermining the principle of pluralism essential to any genuine democratic process”.

# “You can call the process what you like, but not elections,” Bassam Alahmad, executive director of France-based Syrians for Truth and Justice, one of the organisations to have signed the statement, told the AFP news agency.

# Meanwhile, elections in the restive Druze-majority province of Suwayda and in northeastern areas controlled by the Kurdish-led Syrian Democratic Forces have been indefinitely postponed due to tensions between local authorities and the central government in Damascus.

# No campaigns, no parties
# Reporting from Damascus, Al Jazeera’s Osama Bin Javaid said the vote for the new assembly was being held under “a hybrid model between a selection and an election”.

# He said whatever the democratic shortcomings of Sunday’s elections, they were an important step for Syrians towards gaining representation in a body that could begin tackling the country’s significant challenges.

# “There are no political campaigns, there are no political parties,” he said.

# Get instant alerts and updates based on your interests. Be the first to know when big stories happen.
# Yes, keep me updated
# Bin Javaid said the Syrians he had spoken to “realise that this is not a general election, and … are aware that Syria cannot hold a general election” because of the destruction wrought by 14 years of war.

# “But people on the street feel that this is the first chance that they’re getting of a real taste of an election after nearly six decades of the Assad family’s rule,” he added.


# Play Video
# 2:06
# Now Playing
# 02:06
# Syria set for first parliamentary elections since the fall of the Assad regime
# Syria set for first parliamentary elections since the fall of the Assad regime
# Next
# 02:22
# Wave of cyberattacks on telecom giants shakes South Korea’s tech hub reputation
# Wave of cyberattacks on telecom giants shakes South Korea’s tech hub reputation
# 04:59
# Israel intensifies Gaza bombardment for a second day despite US pressure to stop
# Israel intensifies Gaza bombardment for a second day despite US pressure to stop
# 02:18
# Indigenous Raramuri runners showcase endurance in Mexico’s Copper Canyon race
# Indigenous Raramuri runners showcase endurance in Mexico’s Copper Canyon race
# 02:19
# Thousands rally in Rome in solidarity with Gaza, demanding Italy to end arms exports to Israel
# Thousands rally in Rome in solidarity with Gaza, demanding Italy to end arms exports to Israel

# During the al-Assad dynasty’s years in power, regular elections were held, but they were widely viewed as sham, and the al-Assad-led Baath party always dominated the parliament.

# During its 30-month term, the incoming parliament will be tasked with preparing the ground for a popular vote in the next elections.

# Bin Javaid said the parliament would have to prove “that Syria can become a constitutional democracy and the people who come to power will be answerable to those who vote for them”.

# How will it work?
# The People’s Assembly has 210 seats, of which 140 are voted on by electoral colleges throughout the country, with the number of seats for each district distributed by population. The remaining 70 deputies will be appointed directly by al-Sharaa.

# A total of 7,000 electoral college members in 60 districts – chosen from a pool of applicants in each district by committees appointed for the purpose – will vote for the 140 seats.

# However, the postponement of elections in the Kurdish-dominated northeast and Druze-majority southern province of Suwayda, which remain outside Damascus’s control, means that seats there will remain empty.

# All the candidates come from the ranks of the electoral colleges and are running as independents, as existing political parties were dissolved by Syria’s new authorities following al-Assad’s ouster, and no replacement system has been established to register new parties.


# Play Video
# 19:43

# Obstacles to popular vote
# While the lack of a popular vote has been criticised as undemocratic, some analysts say the government’s reasons are valid.

# Al-Sharaa has said it would be impossible to organise direct elections now due to the large number of Syrians who lack documentation after millions fled abroad or were displaced internally.

# “We don’t even know how many Syrians are in Syria today”, because of the large number of displaced people, said Benjamin Feve, a senior research analyst at the Syria-focused Karam Shaar Advisory consulting firm, told The Associated Press news agency.

# “It would be really difficult to draw electoral lists today in Syria.”

# Haid Haid, a senior research fellow at the Arab Reform Initiative and the Chatham House think tank, told AP that he was more concerned by the lack of transparency under which electors were chosen.

# “Especially when it comes to choosing the subcommittees and the electoral colleges, there is no oversight, and the whole process is sort of potentially vulnerable to manipulation,” he said.

# Critics have also expressed concerns about the representation of minorities and women in the new assembly, with only 14 percent of the candidates being women, and Suwayda and the northeast excluded from the process.

# Nishan Ismail, 40, a teacher in the Kurdish-controlled northeast, told AFP that “elections could have been a new political start” after the fall of the al-Assad regime, but “the marginalisation of numerous regions shows that the standards of political participation are not respected”.

# At a meeting in Damascus this week, candidate Mayssa Halwani said the criticism of the system was to be expected. “The government is new to power and freedom is new for us,” she said.

# Al Jazeera’s Bin Javaid said the incoming parliament would face significant challenges in a country still working to dismantle the mechanisms of the al-Assad regime and rebuild itself from scratch.

# These include the economy, which is struggling despite the lifting of international sanctions; security challenges, with Syrian territory under the control of Kurdish forces, Druze fighters and Israel; and the need to provide representation to different groups among the country’s diverse population.

# “Syria needs everything,” he said.


#     """
    
#     result = analyze_text_for_triggers(test_title, test_text)
#     print("\n🎯 FINAL RESULT (Top 3 Phrases):")
#     print(json.dumps(result, indent=2))


# """
# Dynamic trigger-word scanner (LLM-driven) - Returns Top 3 Phrases
# """

# import os
# import sys
# import re
# import json
# from rapidfuzz import fuzz, process
# from groq import Groq
# from dotenv import load_dotenv

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# ENV_PATH = os.path.join(BASE_DIR, ".env")
# load_dotenv(ENV_PATH)

# def safe_json(raw: str) -> dict:
#     """Robust JSON parsing from LLM output"""
#     if not raw:
#         return {"triggers": []}
    
#     cleaned = raw.strip()
#     cleaned = re.sub(r'```json\s*', '', cleaned)
#     cleaned = re.sub(r'```\s*', '', cleaned)
    
#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         print("⚠️ JSON parse failed, extracting phrases...")
        
#         # Extract phrases using regex
#         phrases = re.findall(r'"phrase"\s*:\s*"([^"]+)"', cleaned)
#         if phrases:
#             print(f"✅ Extracted {len(phrases)} phrases")
#             return {"triggers": [{"phrase": p} for p in phrases]}
        
#         return {"triggers": []}

# class LLMClient:
#     def __init__(self):
#         api_key = os.getenv("GROQ_API_KEY")
#         if not api_key:
#             raise RuntimeError("GROQ_API_KEY not set")
        
#         self.client = Groq(api_key=api_key)
#         self.model = os.getenv("MISINFO_MODEL", "llama-3.1-8b-instant")

#     def get_dynamic_triggers(self, article_title: str, article_text: str) -> dict:
#         """Get trigger phrases from LLM - focused on top 3"""
        
#         # Limit text to avoid token overflow
#         text_preview = article_text[:2500].replace('"', "'").replace('\n', ' ').strip()

#         user_prompt = f"""
# Identify ANY genuinely concerning phrases in this article that show clear misinformation, 
# conspiracy theories, or heavy sensationalism. Return ONLY phrases that are clearly problematic. Return ONLY JSON.

# ARTICLE TITLE: {article_title}
# ARTICLE TEXT: {text_preview}

# CRITICAL RULES:

# - Phrases must appear VERBATIM in the text above
# - Choose phrases that are most sensational, misleading, or manipulative
# - Each phrase should be 5+ words long
# - Return ONLY this JSON format, no other text:

# {{
#   "triggers": [
#     {{"phrase": "exact phrase 1 from text"}},
#     {{"phrase": "exact phrase 2 from text"}}, 
#     ...and other phrases
#     // Can be empty if no concerning phrases!
#   ]
# }}
# """

#         try:
#             completion = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=[{"role": "user", "content": user_prompt}],
#                 temperature=0.1,
#                 max_tokens=500,
#             )

#             response = completion.choices[0].message.content.strip()
#             print("----- LLM OUTPUT -----")
#             print(response)
#             return safe_json(response)
            
#         except Exception as e:
#             print(f"❌ LLM request failed: {e}")
#             return {"triggers": []}

# def find_phrase_snippet(phrase: str, text: str) -> str:
#     """Find phrase in text and return context snippet"""
#     if not phrase or not text:
#         return ""
    
#     phrase_lower = phrase.lower()
#     text_lower = text.lower()
    
#     # Exact match
#     idx = text_lower.find(phrase_lower)
#     if idx != -1:
#         start = max(0, idx - 60)
#         end = min(len(text), idx + len(phrase) + 60)
#         snippet = text[start:end].replace("\n", " ").strip()
#         return f"...{snippet}..."
    
#     return ""

# def select_top_phrases(triggers: list, text: str) -> list:
#     """Select and validate top 3 phrases"""
#     valid_phrases = []
    
#     for trigger in triggers:
#         phrase = trigger.get("phrase", "").strip()
#         # Must be at least 4 words and found in text
#         if len(phrase.split()) >= 4:
#             snippet = find_phrase_snippet(phrase, text)
#             if snippet:
#                 valid_phrases.append({
#                     "phrase": phrase,
#                     "snippet": snippet
#                 })
    
#     # Return top 3 valid phrases (or fewer if not enough found)
#     return valid_phrases[:3]

# def analyze_text_for_triggers(title: str, text: str) -> dict:
#     """
#     Analyze text and return exactly 3 best trigger phrases
#     """
#     client = LLMClient()

#     # Get triggers from LLM
#     print("🔄 Getting top 3 triggers from LLM...")
#     triggers_obj = client.get_dynamic_triggers(title, text)
#     raw_triggers = triggers_obj.get("triggers", [])
    
#     print(f"📊 Raw triggers from LLM: {len(raw_triggers)}")
    
#     # Select top 3 valid phrases
#     final_phrases = select_top_phrases(raw_triggers, text)
    
#     print(f"🎯 Final top phrases: {len(final_phrases)}")
    
#     return {
#         "title": title,
#         "model": client.model,
#         "trigger_count_requested": 3,
#         "trigger_count_received": len(raw_triggers),
#         "list_of_phrases": final_phrases,
#     }

# # Simple test
# if __name__ == "__main__":
#     # Test with sample text
#     test_title = "Will Vijay be arrested for Karur stampede? Tamil Nadu Minister responds"
#     test_text = """
#     Two-thirds of Syria’s new parliament will be chosen by electoral colleges, with the rest appointed by interim President Ahmed al-Sharaa.



# 02:06
# Syria set for first parliamentary elections since the fall of the Assad regime


# By Tim Hume and News Agencies

# Published On 5 Oct 2025
# 5 Oct 2025
# Click here to share on social media
# Share

# Save

# Syria is holding parliamentary elections for the first time since the overthrow of longtime ruler Bashar al-Assad, a landmark moment in the country’s fragile transition after nearly 14 years of war.

# Members of Syria’s electoral colleges gathered on Sunday to vote for the new lawmakers in a process being criticised as undemocratic, with a third of the 210 members of the revamped People’s Assembly appointed by interim leader, Ahmed al-Sharaa.

# Recommended Stories
# list of 4 items
# list 1 of 4In his first UN speech, Syria’s al-Sharaa urges end to all sanctions
# list 2 of 4Syrian President al-Sharaa sits down with US general who arrested him
# list 3 of 4Ukraine, Syria restore diplomatic ties after breakdown during Assad regime
# list 4 of 4Ahmed al-Sharaa’s high-stakes bid to remake Syria
# end of list
# The remaining representatives will not be voted on directly by the people, but chosen instead by electoral colleges around the country.

# Critics say the system favours well-connected figures and is likely to keep power concentrated in the hands of Syria’s new rulers, rather than paving the way for genuine democratic change.

# Syrian President Ahmed al-Sharaa
# Interim President Ahmed al-Sharaa will directly appoint one-third of the deputies [File: Stephanie Lecocq/AFP]
# In a joint statement last month, more than a dozen nongovernmental organisations said the process means al-Sharaa “can effectively shape a parliamentary majority composed of individuals he selected or ensured loyalty from”, which risked “undermining the principle of pluralism essential to any genuine democratic process”.

# “You can call the process what you like, but not elections,” Bassam Alahmad, executive director of France-based Syrians for Truth and Justice, one of the organisations to have signed the statement, told the AFP news agency.

# Meanwhile, elections in the restive Druze-majority province of Suwayda and in northeastern areas controlled by the Kurdish-led Syrian Democratic Forces have been indefinitely postponed due to tensions between local authorities and the central government in Damascus.

# No campaigns, no parties
# Reporting from Damascus, Al Jazeera’s Osama Bin Javaid said the vote for the new assembly was being held under “a hybrid model between a selection and an election”.

# He said whatever the democratic shortcomings of Sunday’s elections, they were an important step for Syrians towards gaining representation in a body that could begin tackling the country’s significant challenges.

# “There are no political campaigns, there are no political parties,” he said.

# Get instant alerts and updates based on your interests. Be the first to know when big stories happen.
# Yes, keep me updated
# Bin Javaid said the Syrians he had spoken to “realise that this is not a general election, and … are aware that Syria cannot hold a general election” because of the destruction wrought by 14 years of war.

# “But people on the street feel that this is the first chance that they’re getting of a real taste of an election after nearly six decades of the Assad family’s rule,” he added.


# Play Video
# 2:06
# Now Playing
# 02:06
# Syria set for first parliamentary elections since the fall of the Assad regime
# Syria set for first parliamentary elections since the fall of the Assad regime
# Next
# 02:22
# Wave of cyberattacks on telecom giants shakes South Korea’s tech hub reputation
# Wave of cyberattacks on telecom giants shakes South Korea’s tech hub reputation
# 04:59
# Israel intensifies Gaza bombardment for a second day despite US pressure to stop
# Israel intensifies Gaza bombardment for a second day despite US pressure to stop
# 02:18
# Indigenous Raramuri runners showcase endurance in Mexico’s Copper Canyon race
# Indigenous Raramuri runners showcase endurance in Mexico’s Copper Canyon race
# 02:19
# Thousands rally in Rome in solidarity with Gaza, demanding Italy to end arms exports to Israel
# Thousands rally in Rome in solidarity with Gaza, demanding Italy to end arms exports to Israel

# During the al-Assad dynasty’s years in power, regular elections were held, but they were widely viewed as sham, and the al-Assad-led Baath party always dominated the parliament.

# During its 30-month term, the incoming parliament will be tasked with preparing the ground for a popular vote in the next elections.

# Bin Javaid said the parliament would have to prove “that Syria can become a constitutional democracy and the people who come to power will be answerable to those who vote for them”.

# How will it work?
# The People’s Assembly has 210 seats, of which 140 are voted on by electoral colleges throughout the country, with the number of seats for each district distributed by population. The remaining 70 deputies will be appointed directly by al-Sharaa.

# A total of 7,000 electoral college members in 60 districts – chosen from a pool of applicants in each district by committees appointed for the purpose – will vote for the 140 seats.

# However, the postponement of elections in the Kurdish-dominated northeast and Druze-majority southern province of Suwayda, which remain outside Damascus’s control, means that seats there will remain empty.

# All the candidates come from the ranks of the electoral colleges and are running as independents, as existing political parties were dissolved by Syria’s new authorities following al-Assad’s ouster, and no replacement system has been established to register new parties.


# Play Video
# 19:43

# Obstacles to popular vote
# While the lack of a popular vote has been criticised as undemocratic, some analysts say the government’s reasons are valid.

# Al-Sharaa has said it would be impossible to organise direct elections now due to the large number of Syrians who lack documentation after millions fled abroad or were displaced internally.

# “We don’t even know how many Syrians are in Syria today”, because of the large number of displaced people, said Benjamin Feve, a senior research analyst at the Syria-focused Karam Shaar Advisory consulting firm, told The Associated Press news agency.

# “It would be really difficult to draw electoral lists today in Syria.”

# Haid Haid, a senior research fellow at the Arab Reform Initiative and the Chatham House think tank, told AP that he was more concerned by the lack of transparency under which electors were chosen.

# “Especially when it comes to choosing the subcommittees and the electoral colleges, there is no oversight, and the whole process is sort of potentially vulnerable to manipulation,” he said.

# Critics have also expressed concerns about the representation of minorities and women in the new assembly, with only 14 percent of the candidates being women, and Suwayda and the northeast excluded from the process.

# Nishan Ismail, 40, a teacher in the Kurdish-controlled northeast, told AFP that “elections could have been a new political start” after the fall of the al-Assad regime, but “the marginalisation of numerous regions shows that the standards of political participation are not respected”.

# At a meeting in Damascus this week, candidate Mayssa Halwani said the criticism of the system was to be expected. “The government is new to power and freedom is new for us,” she said.

# Al Jazeera’s Bin Javaid said the incoming parliament would face significant challenges in a country still working to dismantle the mechanisms of the al-Assad regime and rebuild itself from scratch.

# These include the economy, which is struggling despite the lifting of international sanctions; security challenges, with Syrian territory under the control of Kurdish forces, Druze fighters and Israel; and the need to provide representation to different groups among the country’s diverse population.

# “Syria needs everything,” he said.


#     """
    
#     result = analyze_text_for_triggers(test_title, test_text)
#     print("\n🎯 FINAL RESULT (Top 3 Phrases):")
#     print(json.dumps(result, indent=2))
"""
Dynamic trigger-word scanner (LLM-driven) - Returns Top 3 Phrases
Improved version with better error handling and fallbacks
"""

import os
import sys
import re
import json
import time
from rapidfuzz import fuzz, process
from groq import Groq
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

def safe_json(raw: str) -> dict:
    """Robust JSON parsing from LLM output with multiple fallback methods"""
    if not raw:
        return {"triggers": []}
    
    cleaned = raw.strip()
    
    # Remove code blocks and markdown
    cleaned = re.sub(r'```json\s*', '', cleaned)
    cleaned = re.sub(r'```\s*', '', cleaned)
    cleaned = re.sub(r'^\s*\{', '{', cleaned)
    cleaned = re.sub(r'\}\s*$', '}', cleaned)
    
    # Method 1: Direct JSON parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse failed (method 1): {e}")
    
    # Method 2: Extract JSON object using regex
    try:
        json_match = re.search(r'\{[^{}]*"triggers"[^{}]*\[[^{}]*\{[^{}]*"[^{}]*"[^{}]*\}[^{}]*\][^{}]*\}', cleaned)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    # Method 3: Extract phrases using multiple patterns
    phrases = []
    
    # Pattern 1: "phrase": "value"
    phrases.extend(re.findall(r'"phrase"\s*:\s*"([^"]+)"', cleaned))
    
    # Pattern 2: 'phrase': 'value' 
    phrases.extend(re.findall(r"'phrase'\s*:\s*'([^']+)'", cleaned))
    
    # Pattern 3: Look for quoted strings in arrays
    phrases.extend(re.findall(r'\[[^\]]*"([^"]+)"[^\]]*\]', cleaned))
    
    # Pattern 4: Simple quoted strings that look like phrases
    potential_phrases = re.findall(r'"([^"]{10,100})"', cleaned)
    phrases.extend([p for p in potential_phrases if len(p.split()) >= 3])
    
    # Remove duplicates and clean
    unique_phrases = []
    seen = set()
    for phrase in phrases:
        clean_phrase = phrase.strip()
        if clean_phrase and clean_phrase not in seen and len(clean_phrase.split()) >= 3:
            unique_phrases.append(clean_phrase)
            seen.add(clean_phrase)
    
    if unique_phrases:
        print(f"✅ Extracted {len(unique_phrases)} phrases via fallback")
        return {"triggers": [{"phrase": p} for p in unique_phrases]}
    
    return {"triggers": []}

class LLMClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ GROQ_API_KEY not found in environment variables")
            print("💡 Make sure to set GROQ_API_KEY in your .env file")
            raise RuntimeError("GROQ_API_KEY not set")
        
        self.client = Groq(api_key=api_key)
        self.model = os.getenv("MISINFO_MODEL", "llama-3.1-8b-instant")
        print(f"🤖 Using model: {self.model}")

    def get_dynamic_triggers(self, article_title: str, article_text: str, max_retries: int = 2) -> dict:
        """Get trigger phrases from LLM with retry logic"""
        
        # Limit text to avoid token overflow
        text_preview = article_text[:2000].replace('"', "'").replace('\n', ' ').strip()
        
        if len(text_preview) < 100:
            print("⚠️ Article text too short for analysis")
            return {"triggers": []}

        user_prompt = f"""
Analyze this news article and identify the top 3 most concerning phrases that could indicate misinformation, bias, or sensationalism. 
Focus on phrases that are verifiably present in the text.

ARTICLE TITLE: {article_title}
ARTICLE TEXT: {text_preview}

IMPORTANT RULES:
- Select ONLY phrases that appear VERBATIM in the text above
- Choose phrases that are most sensational, misleading, or manipulative
- Each phrase should be 3-15 words long
- Return exactly 3 phrases if possible
- Return ONLY valid JSON format:

{{
  "triggers": [
    {{"phrase": "exact phrase from text"}},
    {{"phrase": "another exact phrase"}},
    {{"phrase": "third exact phrase"}}
  ]
}}

If no concerning phrases are found, return: {{"triggers": []}}
"""

        for attempt in range(max_retries + 1):
            try:
                print(f"🔄 LLM Request (attempt {attempt + 1})...")
                
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": user_prompt}],
                    temperature=0.1,
                    max_tokens=800,
                    timeout=30
                )

                response = completion.choices[0].message.content.strip()
                print("----- LLM RAW OUTPUT -----")
                print(response[:500] + "..." if len(response) > 500 else response)
                print("--------------------------")
                
                parsed = safe_json(response)
                
                # Validate we got some triggers
                triggers = parsed.get("triggers", [])
                if triggers:
                    print(f"✅ LLM returned {len(triggers)} triggers")
                    return parsed
                else:
                    print("⚠️ LLM returned empty triggers list")
                    if attempt < max_retries:
                        print("🔄 Retrying with different parameters...")
                        time.sleep(1)
                        continue
                    return parsed
                
            except Exception as e:
                print(f"❌ LLM request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    print("🔄 Retrying...")
                    time.sleep(2)
                else:
                    return {"triggers": []}
        
        return {"triggers": []}

def find_phrase_snippet(phrase: str, text: str) -> str:
    """Find phrase in text and return context snippet with fuzzy matching"""
    if not phrase or not text:
        return ""
    
    phrase_lower = phrase.lower().strip()
    text_lower = text.lower()
    
    # First try exact match
    idx = text_lower.find(phrase_lower)
    if idx != -1:
        start = max(0, idx - 50)
        end = min(len(text), idx + len(phrase) + 50)
        snippet = text[start:end].replace("\n", " ").strip()
        return f"...{snippet}..."
    
    # Fallback: fuzzy matching for slight variations
    words = phrase_lower.split()
    if len(words) >= 3:
        # Try matching the core part of the phrase
        core_phrase = " ".join(words[:min(5, len(words))])
        idx = text_lower.find(core_phrase)
        if idx != -1:
            start = max(0, idx - 50)
            end = min(len(text), idx + len(core_phrase) + 50)
            snippet = text[start:end].replace("\n", " ").strip()
            return f"...{snippet}..."
    
    return ""

def select_top_phrases(triggers: list, text: str, min_phrases: int = 3) -> list:
    """Select and validate phrases with flexible matching"""
    valid_phrases = []
    
    for trigger in triggers:
        phrase = trigger.get("phrase", "").strip()
        
        # More lenient: at least 3 words
        if len(phrase.split()) >= 3:
            snippet = find_phrase_snippet(phrase, text)
            if snippet:
                valid_phrases.append({
                    "phrase": phrase,
                    "snippet": snippet,
                    "word_count": len(phrase.split())
                })
    
    # Sort by word count (longer phrases are usually better)
    valid_phrases.sort(key=lambda x: x["word_count"], reverse=True)
    
    # Return top phrases
    return valid_phrases[:min_phrases]

def fallback_phrase_extraction(text: str, title: str) -> list:
    """Fallback method when LLM fails - extract concerning phrases using rules"""
    print("🔄 Using fallback phrase extraction...")
    
    # Common concerning patterns
    concerning_patterns = [
        r'\b(conspiracy|cover.?up|suppressed|hidden truth|they don\'t want you to know)\b',
        r'\b(breaking|shocking|exclusive|you won\'t believe|secret)\b',
        r'\b(urgent|emergency|warning|alert|must read)\b',
        r'\b(proven|scientific breakthrough|miracle cure|guaranteed)\b',
        r'\b(elites|deep state|mainstream media|establishment)\b',
        r'\b(viral|trending|everyone is talking about)\b'
    ]
    
    sentences = re.split(r'[.!?]+', text)
    concerning_phrases = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) >= 5:  # Reasonable sentence length
            for pattern in concerning_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    # Take first 10 words as the phrase
                    words = sentence.split()[:10]
                    phrase = " ".join(words)
                    concerning_phrases.append({
                        "phrase": phrase,
                        "snippet": sentence[:100] + "...",
                        "word_count": len(words),
                        "source": "fallback"
                    })
                    break
    
    # Also check title for concerning phrases
    title_words = title.split()
    if len(title_words) >= 3:
        concerning_phrases.append({
            "phrase": title,
            "snippet": title,
            "word_count": len(title_words),
            "source": "title"
        })
    
    return concerning_phrases[:3]  # Return top 3

def analyze_text_for_triggers(title: str, text: str) -> dict:
    """
    Analyze text and return top trigger phrases with robust fallbacks
    """
    print(f"🎯 Analyzing: '{title}'")
    print(f"📝 Text length: {len(text)} characters")
    
    # Initialize client with error handling
    try:
        client = LLMClient()
        use_llm = True
    except Exception as e:
        print(f"❌ LLM client initialization failed: {e}")
        use_llm = False
    
    final_phrases = []
    
    # Try LLM approach first
    if use_llm:
        print("🔄 Getting triggers from LLM...")
        triggers_obj = client.get_dynamic_triggers(title, text)
        raw_triggers = triggers_obj.get("triggers", [])
        
        print(f"📊 Raw triggers from LLM: {len(raw_triggers)}")
        
        # Select valid phrases
        final_phrases = select_top_phrases(raw_triggers, text)
    
    # Fallback if LLM failed or didn't return enough phrases
    if len(final_phrases) < 3:
        print(f"🔄 LLM returned only {len(final_phrases)} phrases, using fallback...")
        fallback_phrases = fallback_phrase_extraction(text, title)
        
        # Combine and deduplicate
        existing_phrases = {p["phrase"] for p in final_phrases}
        for phrase_data in fallback_phrases:
            if phrase_data["phrase"] not in existing_phrases and len(final_phrases) < 3:
                final_phrases.append(phrase_data)
                existing_phrases.add(phrase_data["phrase"])
    
    print(f"🎯 Final top phrases: {len(final_phrases)}")
    
    return {
        "title": title,
        "analysis_method": "llm_with_fallback",
        "trigger_count_requested": 3,
        "trigger_count_delivered": len(final_phrases),
        "triggers": final_phrases,
        "success": len(final_phrases) > 0
    }

# Enhanced test function
if __name__ == "__main__":
    # Test with sample text
    test_title = "Will Vijay be arrested for Karur stampede? Tamil Nadu Minister responds"
    test_text = """
    Two-thirds of Syria's new parliament will be chosen by electoral colleges, with the rest appointed by interim President Ahmed al-Sharaa.

    Syria is holding parliamentary elections for the first time since the overthrow of longtime ruler Bashar al-Assad, a landmark moment in the country's fragile transition after nearly 14 years of war.

    Members of Syria's electoral colleges gathered on Sunday to vote for the new lawmakers in a process being criticised as undemocratic, with a third of the 210 members of the revamped People's Assembly appointed by interim leader, Ahmed al-Sharaa.

    Critics say the system favours well-connected figures and is likely to keep power concentrated in the hands of Syria's new rulers, rather than paving the way for genuine democratic change.

    In a joint statement last month, more than a dozen nongovernmental organisations said the process means al-Sharaa "can effectively shape a parliamentary majority composed of individuals he selected or ensured loyalty from", which risked "undermining the principle of pluralism essential to any genuine democratic process".

    "You can call the process what you like, but not elections," Bassam Alahmad, executive director of France-based Syrians for Truth and Justice, one of the organisations to have signed the statement, told the AFP news agency.
    """
    
    print("🧪 Testing Improved Trigger Scanner\n")
    
    try:
        result = analyze_text_for_triggers(test_title, test_text)
        print("\n🎯 FINAL RESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result["triggers"]:
            print(f"\n📋 Extracted Phrases:")
            for i, trigger in enumerate(result["triggers"], 1):
                print(f"{i}. '{trigger['phrase']}'")
                print(f"   Context: {trigger['snippet']}")
        else:
            print("❌ No triggers found - article may be credible or text too short")
            
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()