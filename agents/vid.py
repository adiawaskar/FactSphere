# import cv2
# import moviepy.editor as mp
# from ultralytics import YOLO
# from groq import Groq
# import os
# from dotenv import load_dotenv

# load_dotenv()

# # =====================
# # STEP 1: Extract Audio
# # =====================
# def extract_audio(video_path, audio_path="temp_audio.wav"):
#     """
#     Extracts audio from a video file and saves it as a WAV file.

#     Args:
#         video_path (str): The path to the input video file.
#         audio_path (str): The path where the extracted audio WAV file will be saved.

#     Returns:
#         str: The path to the saved audio file.
#     """
#     print(f"\n[1] Extracting audio from {video_path}...")
#     try:
#         clip = mp.VideoFileClip(video_path)
#         clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
#         print(f"    -> Audio extracted successfully to {audio_path}")
#         return audio_path
#     except Exception as e:
#         print(f"    -> Error extracting audio: {e}")
#         raise

# # ===================================
# # STEP 2: Convert Audio -> Text (STT) using Groq Whisper
# # ===================================
# def audio_to_text(audio_path, groq_api_key):
#     """
#     Converts an audio file to text using Groq's Whisper API.

#     Args:
#         audio_path (str): The path to the input audio file.
#         groq_api_key (str): Your Groq API key.

#     Returns:
#         str: The transcribed text from the audio.
#     """
#     print(f"\n[2] Converting audio to text using Groq Whisper from {audio_path}...")
#     try:
#         client = Groq(api_key=groq_api_key)
        
#         with open(audio_path, "rb") as file:
#             transcript_response = client.audio.transcriptions.create(
#                 file=file,
#                 model="whisper-large-v3-turbo", # Using Groq's optimized Whisper model
#                 response_format="text"
#             )
#         transcript = transcript_response
#         print(f"    -> Transcription complete. Transcript: \"{transcript[:100]}...\"") # Print first 100 chars
#         return transcript
#     except Exception as e:
#         print(f"    -> Error transcribing audio with Groq: {e}")
#         raise

# # ====================================
# # STEP 3: Extract Visual Context (YOLO)
# # ====================================
# def extract_visual_context(video_path, frame_skip=30):
#     """
#     Extracts detected objects from video frames using a YOLOv8n model.

#     Args:
#         video_path (str): The path to the input video file.
#         frame_skip (int): Number of frames to skip between detections for performance.

#     Returns:
#         list: A list of unique detected object labels (strings).
#     """
#     print(f"\n[3] Extracting visual context from {video_path} using YOLOv8n...")
#     try:
#         model = YOLO("yolov8n.pt")   # lightweight model
#         cap = cv2.VideoCapture(video_path)
        
#         if not cap.isOpened():
#             raise IOError(f"Could not open video file: {video_path}")

#         frame_count = 0
#         detected_objects = set()

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             if frame_count % frame_skip == 0:  # skip frames for speed
#                 results = model(frame, verbose=False) # verbose=False to suppress per-frame logging
#                 for r in results:
#                     for box in r.boxes:
#                         cls_id = int(box.cls[0])
#                         label = model.names[cls_id]
#                         detected_objects.add(label)
#             frame_count += 1

#         cap.release()
#         visuals_list = list(detected_objects)
#         print(f"    -> Visual context extraction complete. Detected {len(visuals_list)} unique objects: {visuals_list}")
#         return visuals_list
#     except Exception as e:
#         print(f"    -> Error extracting visual context: {e}")
#         raise

# # ==========================================
# # STEP 4: Compare Audio Transcript & Visuals
# # ==========================================
# def check_consistency_groq(transcript, visuals, groq_api_key):
#     """
#     Compares the audio transcript and visual objects using Groq LLM to check for consistency.

#     Args:
#         transcript (str): The transcribed text from the video's audio.
#         visuals (list): A list of detected objects from the video's frames.
#         groq_api_key (str): Your Groq API key.

#     Returns:
#         str: The LLM's verdict on consistency (MATCH/MISMATCH) with an explanation.
#     """
#     print("\n[4] Checking consistency with Groq LLM...")
#     try:
#         client = Groq(api_key=groq_api_key)

#         prompt = f"""
# You are an expert fact-checking system. 
# Your task is to detect whether the **audio narration (speech)** of a video 
# matches the **visual scene (objects, activities)**.

# ### Audio Transcript:
# {transcript}

# ### Visual Captions (sampled from video frames):
# {', '.join(visuals) if visuals else "No specific objects detected."}

# ### Instructions:
# 1. Compare the audio transcript with the visual captions.
# 2. If the audio and visuals describe consistent events, output: "MATCH".
# 3. If they describe different or unrelated events, output: "MISMATCH".
# 4. Provide a one-sentence explanation of why.

# Example:
# - Audio: "People protesting and shouting slogans"
# - Visuals: "Cars on a highway, no people visible"
# - Output: "MISMATCH - Audio describes protest but visuals show traffic."

# Now analyze this case:
# """

#         response = client.chat.completions.create(
#             model="llama3-70b-8192", # Using a powerful model for better reasoning
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0 # Low temperature for deterministic, factual responses
#         )
#         verdict = response.choices[0].message.content
#         print(f"    -> Groq LLM consistency check complete. Verdict: {verdict}")
#         return verdict
#     except Exception as e:
#         print(f"    -> Error checking consistency with Groq LLM: {e}")
#         raise

# # ========================
# # MAIN PIPELINE EXECUTION
# # ========================
# def main(video_path, groq_api_key):
#     """
#     Main function to execute the video misinformation detection pipeline.

#     Args:
#         video_path (str): The path to the input video file.
#         groq_api_key (str): Your Groq API key.
#     """
#     temp_audio_file = "temp_audio.wav"
#     try:
#         print("--- Starting video misinformation detection pipeline ---")

#         # Step 1: Extract Audio
#         audio_path = extract_audio(video_path, temp_audio_file)
        
#         # Step 2: Convert Audio -> Text (STT)
#         transcript = audio_to_text(audio_path, groq_api_key)
        
#         # Step 3: Extract Visual Context (YOLO)
#         visuals = extract_visual_context(video_path)
        
#         # Step 4: Compare Audio Transcript & Visuals
#         verdict = check_consistency_groq(transcript, visuals, groq_api_key)
        
#         print("\n--- Pipeline execution finished ---")
#         print(f"\nFinal Verdict for {video_path}:\n{verdict}")

#     except Exception as e:
#         print(f"\nAn error occurred during the pipeline execution: {e}")
#     finally:
#         # Clean up temporary audio file
#         if os.path.exists(temp_audio_file):
#             os.remove(temp_audio_file)
#             print(f"\nCleaned up temporary audio file: {temp_audio_file}")


# # Example usage
# if __name__ == "__main__":
#     # Ensure GROQ_API_KEY is set as an environment variable for security
#     # export GROQ_API_KEY='your_groq_api_key_here'
    
#     GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
#     if not GROQ_API_KEY:
#         print("WARNING: GROQ_API_KEY environment variable not set.")
#         print("Please set it or replace 'None' with your actual key in the script (not recommended for production).")
#         exit(1)

#     VIDEO_PATH = "/Users/keshavdhanuka01/Desktop/MisinfoVerify/FactSphere/videos/news.mov"
    
#     main(VIDEO_PATH, GROQ_API_KEY)

import cv2
import moviepy.editor as mp
from groq import Groq
import os
import torch
from dotenv import load_dotenv
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

load_dotenv()

# =====================
# STEP 1: Extract Audio
# =====================
def extract_audio(video_path, audio_path="temp_audio.wav"):
    """
    Extracts audio from a video file and saves it as a WAV file.
    """
    print(f"\n[1] Extracting audio from {video_path}...")
    try:
        clip = mp.VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        print(f"    -> Audio extracted successfully to {audio_path}")
        return audio_path
    except Exception as e:
        print(f"    -> Error extracting audio: {e}")
        raise

# ===================================
# STEP 2: Convert Audio -> Text (STT) using Groq Whisper
# ===================================
def audio_to_text(audio_path, groq_api_key):
    """
    Converts an audio file to text using Groq's Whisper API.
    """
    print(f"\n[2] Converting audio to text using Groq Whisper from {audio_path}...")
    try:
        client = Groq(api_key=groq_api_key)
        
        with open(audio_path, "rb") as file:
            transcript_response = client.audio.transcriptions.create(
                file=file,
                model="whisper-large-v3-turbo", # Groq's Whisper
                response_format="text"
            )
        transcript = transcript_response
        print(f"    -> Transcription complete. Transcript: \"{transcript[:100]}...\"")
        return transcript
    except Exception as e:
        print(f"    -> Error transcribing audio with Groq: {e}")
        raise

# ====================================
# STEP 3: Extract Visual Context (BLIP Captioning)
# ====================================
def extract_visual_context(video_path, frame_skip=30):
    """
    Extracts natural language captions from video frames using BLIP.
    """
    print(f"\n[3] Extracting visual captions from {video_path} using BLIP...")
    try:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
        model_blip = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Could not open video file: {video_path}")

        frame_count = 0
        captions = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_skip == 0:
                # Convert OpenCV frame (BGR) to PIL (RGB)
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                inputs = processor(images=image, return_tensors="pt")
                with torch.no_grad():
                    out = model_blip.generate(**inputs, max_length=50)
                caption = processor.decode(out[0], skip_special_tokens=True)
                captions.append(caption)

            frame_count += 1

        cap.release()
        print(f"    -> Visual captioning complete. Sample captions: {captions}...")
        return captions
    except Exception as e:
        print(f"    -> Error extracting visual captions: {e}")
        raise

# def extract_visual_context(video_path, hist_thresh=0.6, max_frames=10):
#     """
#     Extracts natural language captions from keyframes using BLIP.
#     Uses histogram-based scene detection to avoid redundant frames.
#     """
#     print(f"\n[3] Extracting visual captions from {video_path} using BLIP with keyframe extraction...")
#     try:
#         processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
#         model_blip = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             raise IOError(f"Could not open video file: {video_path}")

#         prev_hist = None
#         frame_count = 0
#         captions = []
#         keyframes = 0

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             # Compute histogram for current frame
#             hist = cv2.calcHist([frame], [0], None, [256], [0, 256])
#             hist = cv2.normalize(hist, hist).flatten()

#             if prev_hist is not None:
#                 diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
#                 if diff < hist_thresh:  # Scene changed
#                     # Convert frame to PIL
#                     image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#                     inputs = processor(images=image, return_tensors="pt")
#                     with torch.no_grad():
#                         out = model_blip.generate(**inputs, max_length=50)
#                     caption = processor.decode(out[0], skip_special_tokens=True)
#                     captions.append(caption)
#                     keyframes += 1

#                     if keyframes >= max_frames:  # Stop after enough keyframes
#                         break

#             prev_hist = hist
#             frame_count += 1

#         cap.release()
#         print(f"    -> Visual captioning complete. Extracted {len(captions)} keyframe captions.")
#         print(f"       Sample captions: {captions[:3]}...")
#         return captions
#     except Exception as e:
#         print(f"    -> Error extracting visual captions: {e}")
#         raise

# ==========================================
# STEP 4: Compare Audio Transcript & Visuals
# ==========================================
def check_consistency_groq(transcript, visuals, groq_api_key):
    """
    Compares the audio transcript and visual captions using Groq LLM.
    """
    print("\n[4] Checking consistency with Groq LLM...")
    try:
        client = Groq(api_key=groq_api_key)

        prompt = f"""
You are an expert fact-checking system. 
Your task is to detect whether the **audio narration (speech)** of a video 
matches the **visual scene (captions)**.

### Audio Transcript:
{transcript}

### Visual Captions (sampled from video frames):
{'; '.join(visuals) if visuals else "No specific visuals detected."}

### Instructions:
1. Compare the audio transcript with the visual captions.
2. If the audio and visuals describe consistent events, output: "MATCH".
3. If they describe different or unrelated events, output: "MISMATCH".
4. Provide a one-sentence explanation of why.

Now analyze this case:
"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        verdict = response.choices[0].message.content
        print(f"    -> Groq LLM consistency check complete. Verdict: {verdict}")
        return verdict
    except Exception as e:
        print(f"    -> Error checking consistency with Groq LLM: {e}")
        raise

# ========================
# MAIN PIPELINE EXECUTION
# ========================
def main(video_path, groq_api_key):
    temp_audio_file = "temp_audio.wav"
    try:
        print("--- Starting video misinformation detection pipeline ---")

        # Step 1: Extract Audio
        audio_path = extract_audio(video_path, temp_audio_file)
        
        # Step 2: Convert Audio -> Text (STT)
        transcript = audio_to_text(audio_path, groq_api_key)
        
        # Step 3: Extract Visual Context (BLIP Captioning)
        visuals = extract_visual_context(video_path)
        
        # Step 4: Compare Audio Transcript & Visuals
        verdict = check_consistency_groq(transcript, visuals, groq_api_key)
        
        print("\n--- Pipeline execution finished ---")
        print(f"\nFinal Verdict for {video_path}:\n{verdict}")

    except Exception as e:
        print(f"\nAn error occurred during the pipeline execution: {e}")
    finally:
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
            print(f"\nCleaned up temporary audio file: {temp_audio_file}")


# Example usage
if __name__ == "__main__":
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY environment variable not set.")
        exit(1)

    VIDEO_PATH = "/Users/keshavdhanuka01/Desktop/MisinfoVerify/FactSphere/videos/news.mov"
    
    main(VIDEO_PATH, GROQ_API_KEY)