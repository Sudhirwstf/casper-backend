import json
import os
import re
from typing import List, Dict

BUFFER = 3.0

def ends_with_sentence(text: str) -> bool:
    return bool(re.search(r"[.!?][\"']?$", text.strip()))

def get_forward_only_sentence(transcript: List[Dict], start_time: float, end_time: float, buffer: float = BUFFER) -> str:
    context_segments = []
    for i, seg in enumerate(transcript):
        if seg["end"] >= (start_time - buffer):
            for j in range(i, len(transcript)):
                context_segments.append(transcript[j]["text"])
                if ends_with_sentence(transcript[j]["text"]):
                    break
            break
    return " ".join(context_segments).strip()

def extract_captions_for_gaps(transcript: List[Dict], gaps: List[Dict], buffer: float = BUFFER) -> List[Dict]:
    enriched = []
    for seg in gaps:
        context = get_forward_only_sentence(transcript, seg["start"], seg["end"], buffer)
        enriched.append({
            "start": seg["start"],
            "end": seg["end"],
            "context": context
        })
    return enriched

def save_captions(captions: List[Dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(captions, f, indent=2, ensure_ascii=False)

# === CLI testing entry ===
if __name__ == "__main__":
    TRANSCRIPT_PATH = "transcripts/speech_podcast.json"
    GAP_PATH = "output/highlight_timestamps.json"
    OUTPUT_PATH = "temp/gap_contexts.json"

    print("📥 Loading data...")
    with open(TRANSCRIPT_PATH, 'r', encoding='utf-8') as f:
        transcript = json.load(f)
    with open(GAP_PATH, 'r', encoding='utf-8') as f:
        gaps = json.load(f)

    print("🧠 Extracting contextual captions...")
    captions = extract_captions_for_gaps(transcript, gaps)

    print(f"✅ Found {len(captions)} caption segments.")
    save_captions(captions, OUTPUT_PATH)
    print(f"📁 Saved to: {OUTPUT_PATH}")
