import os
import json
from typing import List, Dict

SCORE_THRESHOLD = 0.70  # Minimum score to consider a segment for highlights

def load_json(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: List[Dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def extract_high_scoring_segments(data: List[Dict], threshold: float = SCORE_THRESHOLD) -> List[Dict]:
    return [
        {"start": seg["start"], "end": seg["end"]}
        for seg in data
        if seg.get("final_score", 0) >= threshold
    ]

def extract_highlights_from_file(input_path: str, output_path: str = None, threshold: float = SCORE_THRESHOLD, persist: bool = True) -> List[Dict]:
    data = load_json(input_path)
    highlights = extract_high_scoring_segments(data, threshold)

    if persist and output_path:
        save_json(highlights, output_path)
        print(f"[📁] Saved to: {output_path}")

    return highlights

# === CLI entry ===
if __name__ == "__main__":
    INPUT_PATH = "output/merged_scores.json"
    OUTPUT_PATH = "temp/highlight_timestamps.json"

    print("📥 Loading scored segments...")
    segments = load_json(INPUT_PATH)

    print(f"🎯 Extracting segments with final_score ≥ {SCORE_THRESHOLD}...")
    highlights = extract_high_scoring_segments(segments)

    print(f"✅ Highlight segments found: {len(highlights)}")
    save_json(highlights, OUTPUT_PATH)
    print(f"📁 Saved to: {OUTPUT_PATH}")
