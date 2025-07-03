import os
import json
from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector
from math import exp
from typing import List, Dict


def compute_v_score(duration: float, k: float = 0.5) -> float:
    """
    Compute the visual stagnancy score using exponential scaling.
    """
    return round(1 - exp(-k * duration), 3)


def detect_visual_stagnancy(
    video_path: str,
    threshold: float = 20.0, #30.0,
    k: float = 0.5,
    persist: bool = False,
    output_dir: str = "temp",
    max_chunk: float = 4.0
) -> List[Dict]:
    """
    Detects visually stagnant scenes in a video and scores them.
    Splits long stagnant segments (> max_chunk) into smaller ones.

    Args:
        video_path (str): Input video path.
        threshold (float): SceneDetect sensitivity threshold.
        k (float): Visual stagnancy exponential sensitivity.
        persist (bool): Whether to save results to JSON.
        output_dir (str): Directory to save JSON if persist=True.
        max_chunk (float): Max duration of any stagnant segment (in seconds).

    Returns:
        List[Dict]: List of {start, end, v_score} dicts.
    """
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    stagnant_segments = []

    for start, end in scene_list:
        start_time = start.get_seconds()
        end_time = end.get_seconds()
        duration = end_time - start_time

        if duration < 1.0:
            continue  # Skip very short segments

        current_start = start_time
        while current_start < end_time:
            current_end = min(current_start + max_chunk, end_time)
            chunk_duration = current_end - current_start
            v_score = compute_v_score(chunk_duration, k=k)

            stagnant_segments.append({
                "start": round(current_start, 3),
                "end": round(current_end, 3),
                "v_score": v_score
            })

            current_start = current_end

    if persist:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{base_name}_v_score.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stagnant_segments, f, indent=2)
        print(f"[💾] V-scores saved to {output_path}")

    return stagnant_segments


# Optional standalone test
if __name__ == "__main__":
    VIDEO_PATH = "data/speech_podcast.mp4"
    OUTPUT_DIR = "temp"
    result = detect_visual_stagnancy(
        video_path=VIDEO_PATH,
        threshold=30.0,
        k=0.5,
        persist=True,
        output_dir=OUTPUT_DIR,
        max_chunk=4.0  # You can set this to 5.0 if preferred
    )
    print(f"✅ Extracted {len(result)} visual segments")
