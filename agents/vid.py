import cv2
from moviepy import editor as mp
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
    print(f"\n[1] Extracting audio from {video_path}...")
    try:
        clip = mp.VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        clip.close()
        print(f"    -> Audio extracted successfully to {audio_path}")
        return audio_path
    except Exception as e:
        print(f"    -> Error extracting audio: {e}")
        raise

# ===================================
# STEP 2: Convert Audio -> Text (STT) using Groq Whisper
# ===================================
def audio_to_text(audio_path, groq_api_key):
    print(f"\n[2] Converting audio to text using Groq Whisper from {audio_path}...")
    try:
        client = Groq(api_key=groq_api_key)
        
        with open(audio_path, "rb") as file:
            transcript_response = client.audio.transcriptions.create(
                file=(audio_path, file, "audio/wav"),
                model="whisper-large-v3-turbo", 
                response_format="text"
            )
        transcript = transcript_response  # already plain text
        print(f"    -> Transcription complete. Transcript: \"{transcript[:100]}...\"")
        return transcript
    except Exception as e:
        print(f"    -> Error transcribing audio with Groq: {e}")
        raise

# ====================================
# STEP 3: Extract Visual Context (BLIP Captioning)
# ====================================
def extract_visual_context(video_path, frame_skip=30):
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
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                inputs = processor(images=image, return_tensors="pt")
                with torch.no_grad():
                    out = model_blip.generate(**inputs, max_length=50)
                caption = processor.decode(out[0], skip_special_tokens=True)
                captions.append(caption)

            frame_count += 1

        cap.release()
        print(f"    -> Visual captioning complete. Captured {len(captions)} captions.")
        print(f"       Sample: {captions[:3]}")
        return captions
    except Exception as e:
        print(f"    -> Error extracting visual captions: {e}")
        raise

# ==========================================
# STEP 4: Compare Audio Transcript & Visuals
# ==========================================
def check_consistency_groq(transcript, visuals, groq_api_key):
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
1. If the audio and visuals match, output "MATCH".
2. If they are inconsistent, output "MISMATCH".
3. Give a one-sentence explanation.
"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        verdict = response.choices[0].message.content.strip()
        print(f"    -> Consistency check complete. Verdict: {verdict}")
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

        audio_path = extract_audio(video_path, temp_audio_file)
        transcript = audio_to_text(audio_path, groq_api_key)
        visuals = extract_visual_context(video_path)
        verdict = check_consistency_groq(transcript, visuals, groq_api_key)
        
        print("\n--- Pipeline execution finished ---")
        print(f"\nFinal Verdict for {video_path}:\n{verdict}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
            print(f"\nCleaned up temporary audio file: {temp_audio_file}")


if __name__ == "__main__":
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY environment variable not set.")
        exit(1)

    VIDEO_PATH = "/Users/keshavdhanuka01/Desktop/MisinfoVerify/FactSphere/videos/news.mov"
    main(VIDEO_PATH, GROQ_API_KEY)