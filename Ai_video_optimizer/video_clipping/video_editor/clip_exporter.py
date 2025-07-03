import os
import json
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


def load_transcript(video_path):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    transcript_path = os.path.join("transcripts", f"{base_name}.json")
    if os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def overlay_captions_on_clip(clip, transcript, clip_start, clip_end):
    caption_clips = []
    for entry in transcript:
        if clip_start <= entry["start"] <= clip_end:
            start_time = entry["start"] - clip_start
            end_time = min(entry["end"], clip_end) - clip_start
            caption = (
                TextClip(entry["text"], fontsize=24, color='white', bg_color='black')
                .set_position(("center", "bottom"))
                .set_start(start_time)
                .set_duration(end_time - start_time)
                .resize(width=clip.w * 0.9)
            )
            caption_clips.append(caption)

    if caption_clips:
        return CompositeVideoClip([clip, *caption_clips])
    return clip

def export_top_scenes(
    video_path,
    scored_scenes,
    output_dir="clips",
    top_k=5,
    min_len=25.0,
    max_len=35.0,
    pre_buffer=2.0,
    with_captions=False,
    session_id=None  # New parameter
):
    os.makedirs(output_dir, exist_ok=True)
    video = VideoFileClip(video_path)
    video_duration = video.duration

    transcript = load_transcript(video_path) if with_captions else []

    # Sort scenes by score
    sorted_scenes = sorted(scored_scenes, key=lambda x: x["score"], reverse=True)
    exported = []

    for i, scene in enumerate(sorted_scenes[:top_k]):
        scene_start, scene_end = float(scene["start"]), float(scene["end"])
        scene_mid = (scene_start + scene_end) / 2

        start = max(0, scene_mid - (min_len / 2) - pre_buffer)
        end = min(video_duration, start + max_len)

        if end - start < min_len:
            start = max(0, end - min_len)

        if end - start < min_len:
            print(f"[!] Skipping scene {i} (too short: {end - start:.2f}s)")
            continue

        clip = video.subclip(start, end)

        if with_captions and transcript:
            clip = overlay_captions_on_clip(clip, transcript, start, end)

        # Prefix with session ID if provided
        prefix = f"{session_id}_" if session_id else ""
        filename = f"{prefix}clip_{i+1}_{int(start)}s_{int(end)}s.mp4"
        out_path = os.path.join(output_dir, filename)

        clip.write_videofile(out_path, codec="libx264", audio_codec="aac", logger=None)
        exported.append(out_path)

    return exported


# def export_top_scenes(
#     video_path,
#     scored_scenes,
#     output_dir="clips",
#     top_k=5,
#     min_len=25.0,
#     max_len=35.0,
#     pre_buffer=2.0,
#     with_captions=False
# ):
#     os.makedirs(output_dir, exist_ok=True)
#     video = VideoFileClip(video_path)
#     video_duration = video.duration

#     transcript = load_transcript(video_path) if with_captions else []

#     # Sort scenes by score
#     sorted_scenes = sorted(scored_scenes, key=lambda x: x["score"], reverse=True)
#     exported = []

#     for i, scene in enumerate(sorted_scenes[:top_k]):
#         scene_start, scene_end = float(scene["start"]), float(scene["end"])
#         scene_mid = (scene_start + scene_end) / 2

#         start = max(0, scene_mid - (min_len / 2) - pre_buffer)
#         end = min(video_duration, start + max_len)

#         if end - start < min_len:
#             start = max(0, end - min_len)

#         if end - start < min_len:
#             print(f"[!] Skipping scene {i} (too short: {end - start:.2f}s)")
#             continue

#         clip = video.subclip(start, end)

#         if with_captions and transcript:
#             clip = overlay_captions_on_clip(clip, transcript, start, end)

#         out_path = os.path.join(output_dir, f"clip_{i+1}_{int(start)}s_{int(end)}s.mp4")
#         clip.write_videofile(out_path, codec="libx264", audio_codec="aac", logger=None)
#         exported.append(out_path)

#     return exported


# --- Standalone CLI Test ---
if __name__ == "__main__":
    import sys
    from scene_detector import detect_scenes
    from scorer.visual_scorer import extract_frame_embeddings

    if len(sys.argv) < 2:
        print("Usage: python clip_exporter.py <video_path> [--captions]")
        sys.exit(1)

    video_path = sys.argv[1]
    with_captions = "--captions" in sys.argv

    scenes = detect_scenes(video_path)
    cleaned_scenes, visual_scores = extract_frame_embeddings(video_path, scenes)

    scored = [
        {"start": s[0], "end": s[1], "score": visual_scores[i]}
        for i, s in enumerate(cleaned_scenes)
    ]

    video = VideoFileClip(video_path)
    top_k = max(3, int(video.duration // 30))

    exported = export_top_scenes(
        video_path, scored, top_k=top_k, with_captions=with_captions
    )

    print("\n🎉 Exported Clips:")
    for path in exported:
        print(f"✅ {path}")
