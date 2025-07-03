# classifier/classify_transcript.py

import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI

# === Load environment variables ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in environment.")
client = OpenAI(api_key=api_key)

# === Configure logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def classify_transcript(transcript_text: str) -> str:
    """
    Classifies a transcript into 'educational' or 'entertainment'.
    """
    prompt = f"""Classify the following short video transcript into one of two categories:
1. Educational / Monologue / Conversation
2. Entertainment / Junk / Meme / Non-informative

Only return the label: 'educational' or 'entertainment'.

Transcript:
\"\"\"{transcript_text}\"\"\"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        logger.error(f"❌ Failed to classify transcript: {e}")
        raise

def summarize_transcript(transcript_text: str) -> str:
    """
    Summarizes the transcript into a 1-2 sentence summary.
    """
    prompt = f"""Summarize the overall topic and message of this video in 1-2 sentences.
Use simple language and do not include timestamps or lists.

Transcript:
\"\"\"{transcript_text}\"\"\"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ Failed to summarize transcript: {e}")
        raise

def save_summary(summary: str, base_name: str, output_dir: str = "temp/summaries"):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{base_name}_summary.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"[💾] Summary saved to {path}")
