import os
import json
import random
from moviepy.editor import ImageClip, CompositeVideoClip, VideoFileClip
from moviepy.video.fx.all import fadein, fadeout

# === Config ===
IMAGE_DATA_PATH = "temp/image_prompt_segments.json"
MAX_DURATION = 3.0

def load_segments(data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    segments = []
    for item in data:
        image_path = item["image_path"]
        start = item["start"]
        end = item["end"]
        if os.path.exists(image_path):
            segments.append((image_path, start, end))
    return segments

def apply_zoom_and_fade(clip, zoom_type, duration):
    fade_duration = min(0.3, duration * 0.1)
    clip = fadein(clip, fade_duration).fadeout(fade_duration)

    if zoom_type == "in":
        return clip.resize(lambda t: 1.0 + 0.02 * t)
    else:
        return clip.resize(lambda t: 1.05 - 0.02 * t)

def insert_multiple_images(video_path, image_segments, output_path):
    print("🎞️ Loading base video...")
    video = VideoFileClip(video_path)
    audio = video.audio
    video_size = video.size

    image_clips = []
    for image_path, start_time, end_time in image_segments:
        try:
            sentence_duration = end_time - start_time
            overlay_duration = min(MAX_DURATION, max(0.5, sentence_duration * 0.4))
            mid_point = start_time + (sentence_duration - overlay_duration) / 2
            # mid_point   = max(0, start_time + (sentence_duration - overlay_duration) / 2 - 1.0)

            base_clip = (
                ImageClip(image_path)
                .set_start(mid_point)
                .set_duration(overlay_duration)
                .resize(video_size)
                .set_position("center")
                .set_fps(video.fps)
            )

            zoom_type = random.choice(["in", "out"])
            animated_clip = apply_zoom_and_fade(base_clip, zoom_type, overlay_duration)
            image_clips.append(animated_clip)

        except Exception as e:
            print(f"⚠️ Failed to process image: {image_path} | {e}")

    if not image_clips:
        print("🚫 No valid image clips to overlay.")
        return

    print(f"🎬 Composing final video with {len(image_clips)} overlays...")
    final = (
        CompositeVideoClip([video.without_audio(), *image_clips], size=video.size)
        .set_audio(audio)
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")
    print(f"✅ Enhanced video saved to: {output_path}")

if __name__ == "__main__":
    VIDEO_PATH = "data/speech_podcast.mp4"
    OUTPUT_PATH = "output/speech_podcast-enhanced.mp4"

    print("📥 Loading image segments...")
    segments = load_segments(IMAGE_DATA_PATH)

    print(f"📌 Preparing to inject {len(segments)} animated overlays...")
    insert_multiple_images(VIDEO_PATH, segments, OUTPUT_PATH)
