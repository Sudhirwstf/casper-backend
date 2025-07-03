import os
import json
import subprocess
from openai import OpenAI
import dotenv as python_dotenv

python_dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

def extract_audio(video_path, audio_path):
    if not os.path.exists(audio_path):
        print(f"[🎵] Extracting audio from {video_path}...")
        subprocess.run(["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", audio_path], check=True)
    else:
        print(f"[🎵] Audio already exists at {audio_path}")

def transcribe_video(video_path, output_dir="temp/transcripts", save=True, force=False):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    os.makedirs(output_dir, exist_ok=True)
    transcript_path = os.path.join(output_dir, f"{base_name}.json")
    audio_path = os.path.join(output_dir, f"{base_name}.mp3")

    if os.path.exists(transcript_path) and not force:
        print(f"[📄] Transcript already exists at {transcript_path}")
        with open(transcript_path, "r", encoding="utf-8") as f:
            return json.load(f)

    extract_audio(video_path, audio_path)

    print(f"[🧠] Sending to OpenAI Whisper API...")
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

    segments = transcript.segments or []

    transcript_data = [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in segments
    ]

    if save:
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        print(f"[💾] Transcript saved to {transcript_path}")

    return transcript_data


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <video_path>")
    else:
        video_path = sys.argv[1]
        transcribe_video(video_path)
