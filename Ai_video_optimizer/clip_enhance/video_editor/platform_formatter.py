import os
import io
import argparse
import multiprocessing
import numpy as np
from rembg import remove
from PIL import Image
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip, ImageClip

# Platform-specific formatting settings
PLATFORM_SETTINGS = {
    "instagram": {
        "aspect_ratio": (9, 16),
        "logo_position": ("center", "top"),
        "subtitle_style": {"font": "Arial-Bold", "fontsize": 36, "color": "white"}
    },
    "youtube": {
        "aspect_ratio": (9, 16),
        "logo_position": ("right", "bottom"),
        "subtitle_style": {"font": "Arial-Bold", "fontsize": 40, "color": "yellow"}
    },
    "linkedin": {
        "aspect_ratio": (4, 5),
        "logo_position": ("left", "top"),
        "subtitle_style": {"font": "Arial-Bold", "fontsize": 32, "color": "black"}
    }
}

def resize_and_pad(clip: VideoFileClip, target_aspect: tuple[int, int]) -> CompositeVideoClip:
    orig_w, orig_h = clip.size
    target_ratio = target_aspect[0] / target_aspect[1]
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        new_h = int(orig_w / target_ratio)
        new_w = orig_w
    else:
        new_w = int(orig_h * target_ratio)
        new_h = orig_h

    background = ColorClip(size=(new_w, new_h), color=(0, 0, 0), duration=clip.duration)
    clip = clip.set_position(("center", "center"))
    return CompositeVideoClip([background, clip])

def remove_logo_bg(logo_path: str) -> Image.Image:
    with open(logo_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    return Image.open(io.BytesIO(output_bytes)).convert("RGBA")

def overlay_logo(clip: VideoFileClip, logo_path: str, position: str | tuple, scale: float = 0.12) -> CompositeVideoClip:
    if not logo_path or not os.path.exists(logo_path):
        print("⚠️ Logo path not provided or file does not exist.")
        return clip

    try:
        logo_img = remove_logo_bg(logo_path)
        logo_array = np.array(logo_img)

        logo_clip = (
            ImageClip(logo_array, ismask=False)
            .set_duration(clip.duration)
            .resize(height=int(clip.h * scale))
            .set_position(position)
        )
        return CompositeVideoClip([clip, logo_clip])
    except Exception as e:
        print(f"⚠️ Failed to overlay logo: {e}")
        return clip

def process_for_platform(input_path: str, output_dir: str, platform: str, logo_path: str | None = None):
    if platform not in PLATFORM_SETTINGS:
        print(f"⚠️ Unsupported platform: {platform}")
        return

    settings = PLATFORM_SETTINGS[platform]
    print(f"\n🎯 Formatting for {platform.title()}")

    clip = VideoFileClip(input_path)
    formatted = resize_and_pad(clip, settings["aspect_ratio"])

    if logo_path:
        formatted = overlay_logo(formatted, logo_path, settings["logo_position"])

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_{platform}.mp4")

    formatted.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    print(f"✅ Saved to: {output_path}")

def run_process_for_platform(args_tuple):
    input_path, output_dir, platform, logo_path = args_tuple
    process_for_platform(input_path, output_dir, platform, logo_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format video for platforms like Instagram, YouTube, LinkedIn")
    parser.add_argument("input", help="Path to input video file")
    parser.add_argument("--platform", "-p", nargs="+", default=["instagram"],
                        help="Target platforms (e.g. instagram youtube)")
    parser.add_argument("--logo", "-l", help="Optional path to logo image")
    parser.add_argument("--output", "-o", default="formatted_clips", help="Output directory")

    args = parser.parse_args()

    # Prepare arguments for multiprocessing
    jobs = [
        (args.input, args.output, platform, args.logo)
        for platform in args.platform
    ]

    processes = []
    for job_args in jobs:
        p = multiprocessing.Process(target=run_process_for_platform, args=(job_args,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
