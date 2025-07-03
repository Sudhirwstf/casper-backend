# # import os
# # import argparse
# # from moviepy.editor import VideoFileClip
# # from clip_enhance.clip_enhance import main_short_clip_enhance
# # from video_clipping.video_clipper import video_clipping_pipeline

# # def get_video_duration(video_path: str) -> float:
# #     try:
# #         clip = VideoFileClip(video_path)
# #         return clip.duration  
# #     except Exception as e:
# #         print(f"❌ Failed to load video: {e}")
# #         return 0.0

# # def main():
# #     parser = argparse.ArgumentParser(description="🎬 Unified Video Enhancement & Clipping Pipeline")
# #     parser.add_argument("video_path", help="Path to the input video file")
# #     parser.add_argument("--captions", action="store_true", help="Overlay captions (for long videos)")

# #     args = parser.parse_args()
# #     video_path = args.video_path

# #     if not os.path.exists(video_path):
# #         print("❌ Provided video path does not exist.")
# #         return

# #     duration = get_video_duration(video_path)
# #     print(f"⏱️ Video duration: {duration:.2f} seconds")

# #     if duration < 200:  
# #         print("✨ Short video detected — running Clip Enhance pipeline...")
# #         main_short_clip_enhance(video_path)
# #     else:
# #         print("🎯 Long video detected — running Highlight Clipping pipeline...")
# #         video_clipping_pipeline(video_path, with_captions=args.captions)

# # if __name__ == "__main__":
# #     main()

# import os
# import argparse
# import uuid
# from moviepy.editor import VideoFileClip
# from clip_enhance.clip_enhance import main_short_clip_enhance
# from video_clipping.video_clipper import video_clipping_pipeline

# def get_video_duration(video_path: str) -> float:
#     try:
#         clip = VideoFileClip(video_path)
#         return clip.duration
#     except Exception as e:
#         print(f"❌ Failed to load video: {e}")
#         return 0.0

# def print_usage_guide():
#     print("\n📖 USAGE GUIDE:")
#     print("Short videos (< 200s): Run Clip Enhance pipeline")
#     print("  ➤ Optional: --logo path/to/logo.png --platforms instagram youtube")
#     print("Long videos (>= 200s): Run Video Clipping pipeline")
#     print("  ➤ Optional: --captions (to overlay transcript captions)\n")

# def main():
#     parser = argparse.ArgumentParser(description="🎬 Unified Video Enhancement & Clipping Pipeline")
#     parser.add_argument("video_path", help="Path to the input video file")
#     parser.add_argument("--captions", action="store_true", help="Overlay captions (only for long videos)")
#     parser.add_argument("--logo", help="Path to logo image (only for short videos)")
#     parser.add_argument("--platforms", nargs="+", help="Target platforms like instagram, youtube, etc. (only for short videos)")
#     args = parser.parse_args()

#     video_path = args.video_path
#     print_usage_guide()

#     if not os.path.exists(video_path):
#         print("❌ Provided video path does not exist.")
#         return

#     session_id = str(uuid.uuid4())
#     print(f"🆔 Starting new processing session: {session_id}")

#     duration = get_video_duration(video_path)
#     print(f"⏱️ Video duration: {duration:.2f} seconds")

#     if duration < 200:
#         print("✨ Short video detected — running Clip Enhance pipeline...")
#         main_short_clip_enhance(
#             video_path=video_path,
#             logo_path=args.logo,
#             platforms=args.platforms,
#             session_id=session_id
#         )
#     else:
#         print("🎯 Long video detected — running Highlight Clipping pipeline...")
#         video_clipping_pipeline(
#             video_path=video_path,
#             with_captions=args.captions,
#             session_id=session_id
#         )

# if __name__ == "__main__":
#     main()
import os
import argparse
import uuid
import json
from moviepy.editor import VideoFileClip
from clip_enhance.clip_enhance import main_short_clip_enhance
from video_clipping.video_clipper import video_clipping_pipeline
from dotenv import load_dotenv

load_dotenv()

def get_video_duration(video_path: str) -> float:
    try:
        clip = VideoFileClip(video_path)
        return clip.duration
    except Exception as e:
        print(f"❌ Failed to load video: {e}")
        return 0.0

def print_usage_guide():
    print("\n📖 USAGE GUIDE:")
    print("Short videos (< 200s): Run Clip Enhance pipeline")
    print("  ➤ Optional: --logo path/to/logo.png --platforms instagram youtube")
    print("Long videos (>= 200s): Run Video Clipping pipeline")
    print("  ➤ Optional: --captions (to overlay transcript captions)\n")

def save_session_metadata(session_id: str):
    metadata = {"uuid": session_id}
    os.makedirs("output", exist_ok=True)
    session_file = os.path.join("output", f"session_{session_id}.json")
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"📝 Session UUID saved to: {session_file}")

def main():
    parser = argparse.ArgumentParser(description="🎬 Unified Video Enhancement & Clipping Pipeline")
    parser.add_argument("video_path", help="Path to the input video file")
    parser.add_argument("--captions", action="store_true", help="Overlay captions (only for long videos)")
    parser.add_argument("--logo", help="Path to logo image (only for short videos)")
    parser.add_argument("--platforms", nargs="+", help="Target platforms like instagram, youtube, etc. (only for short videos)")
    args = parser.parse_args()

    video_path = args.video_path
    print_usage_guide()

    if not os.path.exists(video_path):
        print("❌ Provided video path does not exist.")
        return

    session_id = str(uuid.uuid4())
    print(f"🆔 Starting new processing session: {session_id}")

    duration = get_video_duration(video_path)
    print(f"⏱️ Video duration: {duration:.2f} seconds")

    if duration < 200:
        print("✨ Short video detected — running Clip Enhance pipeline...")

        # Save session file first
        save_session_metadata(session_id)

        # Enhance and format
        main_short_clip_enhance(
            video_path=video_path,
            logo_path=args.logo,
            platforms=args.platforms,
            session_id=session_id
        )

        # Generate platform-specific metadata using OpenAI
        try:
            from generate_metadata import update_session_json
            update_session_json(session_id)
        except Exception as e:
            print(f"⚠️ Failed to generate platform metadata: {e}")

    else:
        print("🎯 Long video detected — running Highlight Clipping pipeline...")
        video_clipping_pipeline(
            video_path=video_path,
            with_captions=args.captions,
            session_id=session_id
        )

        # Save session metadata only for long videos
        save_session_metadata(session_id)

if __name__ == "__main__":
    main()
