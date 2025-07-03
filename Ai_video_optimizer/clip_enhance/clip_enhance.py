# import os
# import json
# import shutil
# import argparse

# from clip_enhance.transcripts.transcriber import transcribe_video
# from clip_enhance.classifier.classify_transcript import classify_transcript, summarize_transcript
# from clip_enhance.gap_detector.scorer.contextual_gap_detector import score_transcript_chunks
# from clip_enhance.gap_detector.scorer.visual_gap_detector import detect_visual_stagnancy
# from clip_enhance.gap_detector.scorer.scorer import merge_scores
# from clip_enhance.gap_detector.gap_detector import extract_high_scoring_segments
# from clip_enhance.transcripts.clip_transcript import extract_captions_for_gaps, get_forward_only_sentence
# from clip_enhance.generator.image_generator import generate_images_for_gaps
# from clip_enhance.video_editor.injector import insert_multiple_images
# from clip_enhance.video_editor.platform_formatter import process_for_platform

# # === Config ===
# TEMP_DIR = "temp"
# TRANSCRIPTS_DIR = os.path.join(TEMP_DIR, "transcripts")
# IMAGES_DIR = os.path.join(TEMP_DIR, "images")
# OUTPUT_VIDEO_DIR = "output"
# CLEAN_TEMP_FILES = False

# os.makedirs(TEMP_DIR, exist_ok=True)

# def save_json(data, path):
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, 'w', encoding='utf-8') as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)

# def load_json(path):
#     with open(path, 'r', encoding='utf-8') as f:
#         return json.load(f)

# def clean_temp():
#     if CLEAN_TEMP_FILES and os.path.exists(TEMP_DIR):
#         shutil.rmtree(TEMP_DIR)
#         print("🧹 Temporary files cleaned up.")

# def main_short_clip_enhance(video_path, logo_path=None, platforms=None, session_id=None):
#     print(f"\n🎬 Processing: {video_path}")
#     base_name = os.path.splitext(os.path.basename(video_path))[0]
#     prefix = f"{session_id}_" if session_id else ""

#     # Step 1: Transcribe
#     transcript = transcribe_video(video_path, output_dir=TRANSCRIPTS_DIR, force=True)
#     print(f"[📄] Transcript loaded: {len(transcript)} segments")

#     # Step 2: Classify
#     transcript_text = " ".join([seg["text"] for seg in transcript])
#     label = classify_transcript(transcript_text)
#     print(f"[✅] Classified as: {label}")

#     if label != "educational":
#         print("[🚫] Skipping enhancement. Not educational.")
#         return

#     summary = summarize_transcript(transcript_text)
#     print(f"[📘] Summary: {summary}")

#     c_scored = score_transcript_chunks(transcript)
#     c_score_path = os.path.join(TEMP_DIR, f"{prefix}c_score.json")
#     save_json(c_scored, c_score_path)

#     v_scored = detect_visual_stagnancy(video_path, persist=False, max_chunk=4.0)
#     v_score_path = os.path.join(TEMP_DIR, f"{prefix}v_score.json")
#     save_json(v_scored, v_score_path)

#     merged_path = os.path.join(TEMP_DIR, f"{prefix}{base_name}_merged_scores.json")
#     merge_scores(c_score_path, v_score_path, merged_path)

#     merged_data = load_json(merged_path)
#     gaps = extract_high_scoring_segments(merged_data)
#     print(f"[🎯] Found {len(gaps)} enhancement-worthy segments.")

#     enriched_segments = []
#     for seg in gaps:
#         context = get_forward_only_sentence(transcript, seg["start"], seg["end"])
#         enriched_segments.append({**seg, "context": context})

#     image_data = generate_images_for_gaps(enriched_segments, summary, output_dir=IMAGES_DIR)

#     segments = []
#     for idx, item in enumerate(image_data):
#         image_path = os.path.join(IMAGES_DIR, f"gap_{idx}.png")
#         segments.append((image_path, item["start"], item["end"]))

#     # Step 11: Inject visuals
#     output_video_path = os.path.join(OUTPUT_VIDEO_DIR, f"{prefix}{base_name}-enhanced.mp4")
#     insert_multiple_images(video_path, segments, output_video_path)
#     print(f"✅ Final enhanced video saved to: {output_video_path}")

#     # Step 12: Optional formatting for platforms
#     if platforms:
#         for platform in platforms:
#             process_for_platform(
#                 input_path=output_video_path,
#                 output_dir=os.path.join(OUTPUT_VIDEO_DIR, "formatted"),
#                 platform=platform,
#                 logo_path=logo_path
#             )

#     clean_temp()

# # Optional CLI usage (still works as standalone)
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Enhance and format educational short videos.")
#     parser.add_argument("video_path", help="Path to the input video")
#     parser.add_argument("--logo", help="Optional path to logo image")
#     parser.add_argument("--platforms", nargs="+", help="Target platforms like instagram youtube linkedin")
#     parser.add_argument("--session_id", help="Optional session ID to prefix outputs")

#     args = parser.parse_args()
#     main_short_clip_enhance(args.video_path, logo_path=args.logo, platforms=args.platforms, session_id=args.session_id)


import os
import json
import shutil
import argparse

from clip_enhance.transcripts.transcriber import transcribe_video
from clip_enhance.classifier.classify_transcript import classify_transcript, summarize_transcript
from clip_enhance.gap_detector.scorer.contextual_gap_detector import score_transcript_chunks
from clip_enhance.gap_detector.scorer.visual_gap_detector import detect_visual_stagnancy
from clip_enhance.gap_detector.scorer.scorer import merge_scores
from clip_enhance.gap_detector.gap_detector import extract_high_scoring_segments
from clip_enhance.transcripts.clip_transcript import extract_captions_for_gaps, get_forward_only_sentence
from clip_enhance.generator.image_generator import generate_images_for_gaps
from clip_enhance.video_editor.injector import insert_multiple_images
from clip_enhance.video_editor.platform_formatter import process_for_platform

# === Config ===
TEMP_DIR = "temp"
TRANSCRIPTS_DIR = os.path.join(TEMP_DIR, "transcripts")
IMAGES_DIR = os.path.join(TEMP_DIR, "images")
OUTPUT_VIDEO_DIR = "output"
CLEAN_TEMP_FILES = False

os.makedirs(TEMP_DIR, exist_ok=True)

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_temp():
    if CLEAN_TEMP_FILES and os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        print("🧹 Temporary files cleaned up.")

def main_short_clip_enhance(video_path, logo_path=None, platforms=None, session_id=None):
    print(f"\n🎬 Processing: {video_path}")
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    prefix = f"{session_id}_" if session_id else ""

    # Step 1: Transcribe
    transcript = transcribe_video(video_path, output_dir=TRANSCRIPTS_DIR, force=True)
    print(f"[📄] Transcript loaded: {len(transcript)} segments")

    # Step 2: Classify
    transcript_text = " ".join([seg["text"] for seg in transcript])
    label = classify_transcript(transcript_text)
    print(f"[✅] Classified as: {label}")

    if label != "educational":
        print("[🚫] Skipping enhancement. Not educational.")
        return

    # Step 3: Summarize and Save Summary
    summary = summarize_transcript(transcript_text)
    print(f"[📘] Summary: {summary}")

    summary_path = os.path.join(TEMP_DIR, f"{prefix}summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    # Step 4: Score Transcript and Visuals
    c_scored = score_transcript_chunks(transcript)
    c_score_path = os.path.join(TEMP_DIR, f"{prefix}c_score.json")
    save_json(c_scored, c_score_path)

    v_scored = detect_visual_stagnancy(video_path, persist=False, max_chunk=4.0)
    v_score_path = os.path.join(TEMP_DIR, f"{prefix}v_score.json")
    save_json(v_scored, v_score_path)

    # Step 5: Merge Scores
    merged_path = os.path.join(TEMP_DIR, f"{prefix}{base_name}_merged_scores.json")
    merge_scores(c_score_path, v_score_path, merged_path)

    # Step 6: Extract gaps
    merged_data = load_json(merged_path)
    gaps = extract_high_scoring_segments(merged_data)
    print(f"[🎯] Found {len(gaps)} enhancement-worthy segments.")

    # Step 7: Get context
    enriched_segments = []
    for seg in gaps:
        context = get_forward_only_sentence(transcript, seg["start"], seg["end"])
        enriched_segments.append({**seg, "context": context})

    # Step 8: Generate images
    image_data = generate_images_for_gaps(enriched_segments, summary, output_dir=IMAGES_DIR)

    segments = []
    for idx, item in enumerate(image_data):
        image_path = os.path.join(IMAGES_DIR, f"gap_{idx}.png")
        segments.append((image_path, item["start"], item["end"]))

    # Step 9: Inject visuals
    output_video_path = os.path.join(OUTPUT_VIDEO_DIR, f"{prefix}{base_name}-enhanced.mp4")
    insert_multiple_images(video_path, segments, output_video_path)
    print(f"✅ Final enhanced video saved to: {output_video_path}")

    # Step 10: Optional platform formatting
    if platforms:
        for platform in platforms:
            process_for_platform(
                input_path=output_video_path,
                output_dir=os.path.join(OUTPUT_VIDEO_DIR, "formatted"),
                platform=platform,
                logo_path=logo_path
            )

    clean_temp()

# Optional CLI usage (still works as standalone)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhance and format educational short videos.")
    parser.add_argument("video_path", help="Path to the input video")
    parser.add_argument("--logo", help="Optional path to logo image")
    parser.add_argument("--platforms", nargs="+", help="Target platforms like instagram youtube linkedin")
    parser.add_argument("--session_id", help="Optional session ID to prefix outputs")

    args = parser.parse_args()
    main_short_clip_enhance(args.video_path, logo_path=args.logo, platforms=args.platforms, session_id=args.session_id)
