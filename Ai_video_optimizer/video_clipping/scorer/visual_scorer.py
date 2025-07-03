import os
import cv2
import torch
import clip
import numpy as np
from PIL import Image
from tqdm import tqdm
from moviepy.editor import VideoFileClip

device = "cuda" if torch.cuda.is_available() else "cpu"

def load_clip_model():
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess

model, preprocess = load_clip_model()


def extract_frame_embeddings(video_path, scenes, frames_dir="frames"):
    """
    Extract CLIP image embeddings from video frames in each scene.
    Score scenes by visual variance (higher = more visually dynamic).

    Args:
        video_path (str): Path to input video.
        scenes (list): List of (start, end) scene timestamps in seconds.
        frames_dir (str): Directory to save temp frames (optional).

    Returns:
        cleaned_scenes: Top-N (start, end) scene tuples.
        visual_scores: Corresponding variance scores.
    """
    os.makedirs(frames_dir, exist_ok=True)
    video = VideoFileClip(video_path)
    scene_scores = []

    for i, (start, end) in enumerate(tqdm(scenes, desc="📊 Scoring scenes (CLIP)")):
        duration = end - start
        if duration <= 0:
            continue

        embeddings = []
        frame_count = max(1, int(duration))  # Ensure at least 1 frame

        for t in range(frame_count):
            time_sec = start + (t * duration / frame_count)  # Spread sampling
            try:
                frame = video.get_frame(time_sec)
                image = Image.fromarray(frame)
                image_tensor = preprocess(image).unsqueeze(0).to(device)

                with torch.no_grad():
                    embedding = model.encode_image(image_tensor).cpu().numpy().squeeze()
                    embeddings.append(embedding)
            except Exception as e:
                print(f"[!] Frame error at {time_sec:.2f}s: {e}")

        if len(embeddings) >= 2:
            embeddings = np.stack(embeddings)
            variance = float(np.mean(np.var(embeddings, axis=0)))
        else:
            variance = 0.0

        scene_scores.append({"start": start, "end": end, "score": variance})

    # Sort scenes by visual richness
    sorted_scenes = sorted(scene_scores, key=lambda s: s["score"], reverse=True)

    # Dynamic top_k based on video duration
    total_duration = video.duration or 1
    top_k = max(3, int(total_duration / 120))  # 1 per 2 mins, minimum 3

    top_scenes = sorted_scenes[:top_k] if len(sorted_scenes) >= top_k else sorted_scenes
    cleaned_scenes = [(s["start"], s["end"]) for s in top_scenes]
    visual_scores = [s["score"] for s in top_scenes]

    return cleaned_scenes, visual_scores


# Optional CLI test
if __name__ == "__main__":
    import sys
    from scene_detector import detect_scenes

    if len(sys.argv) < 2:
        print("Usage: python visual_scorer.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    scenes = detect_scenes(video_path)

    cleaned_scenes, visual_scores = extract_frame_embeddings(video_path, scenes)

    print("\n🔝 Top Visual Scenes:\n")
    for i, (start, end) in enumerate(cleaned_scenes):
        print(f"▶ {start:.1f}s → {end:.1f}s | Score: {visual_scores[i]:.5f}")
