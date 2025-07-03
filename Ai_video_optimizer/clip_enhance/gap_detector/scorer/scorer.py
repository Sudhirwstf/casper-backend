import os
import json
from typing import List, Dict

def load_json(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: List[Dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def merge_scores_from_data(c_data: List[Dict], v_data: List[Dict]) -> List[Dict]:
    """
    Merges contextual and visual scores into final highlight segments.
    """
    merged = []

    for v_segment in v_data:
        v_start = v_segment["start"]
        v_end = v_segment["end"]
        v_score = v_segment["v_score"]

        # Find overlapping transcript segments
        c_chunks = [
            c for c in c_data
            if not (c["end"] < v_start or c["start"] > v_end)
        ]

        if not c_chunks:
            final_score = round(0.7 * v_score, 3)
            merged.append({
                "start": v_start,
                "end": v_end,
                "v_score": v_score,
                "c_score": 0.0,
                "final_score": final_score
            })
            continue

        avg_c = sum(chunk["c_score"] for chunk in c_chunks) / len(c_chunks)
        final_score = round(0.7 * v_score + 0.3 * avg_c, 3)

        merged.append({
            "start": v_start,
            "end": v_end,
            "v_score": v_score,
            "c_score": round(avg_c, 3),
            "final_score": final_score
        })

    return merged

def merge_scores(c_path: str, v_path: str, output_path: str = None, persist: bool = True) -> List[Dict]:
    """
    Loads visual/contextual scores from file, merges them, and optionally saves.
    Returns merged list.
    """
    c_data = load_json(c_path)
    v_data = load_json(v_path)
    merged = merge_scores_from_data(c_data, v_data)

    if persist and output_path:
        save_json(merged, output_path)
        print(f"[✅] Merged {len(merged)} segments saved to {output_path}")

    return merged

# === CLI Entry Point ===
if __name__ == "__main__":
    c_path = "output/scored_transcript.json"
    v_path = "output/speech_podcast_v_score.json"
    output_path = "temp/merged_scores.json"

    merge_scores(c_path, v_path, output_path)
