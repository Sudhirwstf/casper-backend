import os
import json
import subprocess
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_audio(video_path, audio_path):
    if not os.path.exists(audio_path):
        print(f"[🎵] Extracting audio from {video_path}...")
        subprocess.run(["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", audio_path], check=True)
    else:
        print(f"[🎵] Audio already exists at {audio_path}")

def transcribe_video(video_path, output_dir="transcripts", force=False):
    """
    Transcribes the given video using OpenAI Whisper API and saves transcript to disk.

    Args:
        video_path (str): Path to the input video file.
        output_dir (str): Directory where the transcript will be saved.
        force (bool): If False, will skip transcription if output already exists.

    Returns:
        list: List of transcript segments [{start, end, text}]
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    transcript_path = os.path.join(output_dir, f"{base_name}.json")
    audio_path = os.path.join(output_dir, f"{base_name}.mp3")

    if os.path.exists(transcript_path) and not force:
        with open(transcript_path, "r", encoding="utf-8") as f:
            print(f"[ℹ️] Using cached transcript at {transcript_path}")
            return json.load(f)

    extract_audio(video_path, audio_path)

    print(f"[🧠] Sending audio to OpenAI Whisper API...")
    with open(audio_path, "rb") as audio_file:
        try:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        except Exception as e:
            print(f"[❌] Error during transcription: {e}")
            return []

    segments = transcript.segments or []

    results = [
        {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        }
        for segment in segments
    ]

    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[💾] Transcript saved to {transcript_path}")
    return results

# CLI Usage
if __name__ == "__main__":
    import sys
    from pprint import pprint

    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <video_path>")
        exit(1)

    video_path = sys.argv[1]
    transcript = transcribe_video(video_path)
    pprint(transcript[:5])  # Print first 5 segments
