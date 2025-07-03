# import sys
# import argparse
# import concurrent.futures

# from video_clipping.transcripts.transcriber import transcribe_video
# from video_clipping.scene_detector.scene_detector import detect_scenes
# from video_clipping.scorer.visual_scorer import extract_frame_embeddings
# from video_clipping.video_editor.clip_exporter import export_top_scenes
# from video_clipping.scorer.context_scorer import score_transcript, map_context_scores_to_scenes

# def video_clipping_pipeline(video_path, with_captions=False):
#     print(f"\n🎥 Starting highlight clipping pipeline for: {video_path}")

#     print("🔊 Transcribing audio...")
#     transcript = transcribe_video(video_path)
#     print(f"📝 {len(transcript)} transcript segments detected.")

#     print("🎬 Detecting visual scenes...")
#     scenes = detect_scenes(video_path)
#     print(f"📸 {len(scenes)} scenes detected.")

#     print("⚡ Scoring context and visual diversity in parallel...")
#     with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
#         future_context = executor.submit(score_transcript, transcript)
#         future_visual = executor.submit(extract_frame_embeddings, video_path, scenes)

#         context_scores = future_context.result()
#         cleaned_scenes, visual_scores = future_visual.result()

#     print("🔗 Mapping context + visual scores to scenes...")
#     scored_scenes = map_context_scores_to_scenes(
#         cleaned_scenes, transcript, context_scores, visual_scores
#     )

#     print("✂️ Exporting top video clips...")
#     exported = export_top_scenes(video_path, scored_scenes, with_captions=with_captions)

#     print("\n✅ DONE — Exported Clips:")
#     for path in exported:
#         print(f"📁 {path}")


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Generate educational highlight clips from long videos.")
#     parser.add_argument("video_path", help="Path to input video file")
#     parser.add_argument("--captions", action="store_true", help="Overlay transcript captions on clips")
#     args = parser.parse_args()

#     video_clipping_pipeline(args.video_path, with_captions=args.captions)


import sys
import argparse
import concurrent.futures

from video_clipping.transcripts.transcriber import transcribe_video
from video_clipping.scene_detector.scene_detector import detect_scenes
from video_clipping.scorer.visual_scorer import extract_frame_embeddings
from video_clipping.video_editor.clip_exporter import export_top_scenes
from video_clipping.scorer.context_scorer import score_transcript, map_context_scores_to_scenes

def video_clipping_pipeline(video_path, with_captions=False, session_id=None):
    print(f"\n🎥 Starting highlight clipping pipeline for: {video_path}")
    if session_id:
        print(f"🔑 Session ID: {session_id}")

    print("🔊 Transcribing audio...")
    transcript = transcribe_video(video_path)
    print(f"📝 {len(transcript)} transcript segments detected.")

    print("🎬 Detecting visual scenes...")
    scenes = detect_scenes(video_path)
    print(f"📸 {len(scenes)} scenes detected.")

    print("⚡ Scoring context and visual diversity in parallel...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_context = executor.submit(score_transcript, transcript)
        future_visual = executor.submit(extract_frame_embeddings, video_path, scenes)

        context_scores = future_context.result()
        cleaned_scenes, visual_scores = future_visual.result()

    print("🔗 Mapping context + visual scores to scenes...")
    scored_scenes = map_context_scores_to_scenes(
        cleaned_scenes, transcript, context_scores, visual_scores
    )

    print("✂️ Exporting top video clips...")
    exported = export_top_scenes(video_path, scored_scenes, with_captions=with_captions, session_id=session_id)

    print("\n✅ DONE — Exported Clips:")
    for path in exported:
        print(f"📁 {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate educational highlight clips from long videos.")
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument("--captions", action="store_true", help="Overlay transcript captions on clips")
    parser.add_argument("--session_id", help="Optional session ID to prefix exported clips")
    args = parser.parse_args()

    video_clipping_pipeline(args.video_path, with_captions=args.captions, session_id=args.session_id)
