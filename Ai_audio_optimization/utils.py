import os
import json
from openai import OpenAI
from pydub import AudioSegment  # type: ignore
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def generate_transcription_and_timestamps(model, audio_path):
#     """
#     Transcribe audio using Whisper with word timestamps.
#     Returns (full_text, words) where words is a list of dicts with 'word', 'start', 'end'.
#     """
#     print("🎙️ Transcribing audio...")
#     result = model.transcribe(audio_path, word_timestamps=True)
#     full_text = result["text"].strip()

#     words = []
#     for segment in result["segments"]:
#         for word_info in segment.get("words", []):
#             words.append({
#                 "word": word_info["word"].strip(),
#                 "start": round(word_info["start"], 2),
#                 "end": round(word_info["end"], 2)
#             })

#     return full_text, words

# def save_transcript_text(text, path):
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, "w", encoding="utf-8") as f:
#         f.write(text)
#     print(f"📝 Transcription saved to: {path}")

# def save_word_timestamps(words, path):
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(words, f, indent=2)
#     print(f"🕒 Word timestamps saved to: {path}")

# def save_transcript_metadata(uuid_str, output_dir="output"):
#     """
#     Saves a JSON metadata file with the transcript UUID.

#     Args:
#         uuid_str (str): UUID associated with the transcript.
#         output_dir (str): Directory to save the metadata file.
#     """
#     os.makedirs(output_dir, exist_ok=True)
#     metadata_path = os.path.join(output_dir, f"{uuid_str}_meta.json")
#     metadata = {"transcript_uuid": uuid_str}

#     with open(metadata_path, "w", encoding="utf-8") as f:
#         json.dump(metadata, f, indent=2)

#     print(f"🧾 Metadata saved to: {metadata_path}")


def generate_transcription_and_timestamps(audio_path):
    """
    Transcribe audio using OpenAI Whisper API.
    Returns (full_text, words) where words is a list of dicts with 'word', 'start', 'end'.
    """
    print("🎙️ Transcribing audio...")

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )

    full_text = transcription.text.strip()
    words = []
    for segment in transcription.segments:
        if hasattr(segment, "words"):
            for word_info in segment.words:
                words.append({
                    "word": word_info.word.strip(),
                    "start": round(word_info.start, 2),
                    "end": round(word_info.end, 2)
                })

    return full_text, words


def save_transcript_text(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"📝 Transcription saved to: {path}")


def save_word_timestamps(words, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2)
    print(f"🕒 Word timestamps saved to: {path}")


def save_transcript_metadata(uuid_str, output_dir="output"):
    """
    Saves a JSON metadata file with the transcript UUID.

    Args:
        uuid_str (str): UUID associated with the transcript.
        output_dir (str): Directory to save the metadata file.
    """
    os.makedirs(output_dir, exist_ok=True)
    metadata_path = os.path.join(output_dir, f"{uuid_str}_meta.json")
    metadata = {"transcript_uuid": uuid_str}

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"🧾 Metadata saved to: {metadata_path}")

def remove_non_word_regions(audio_path, words, filler_words, buffer_sec=0.05, fade_ms=20):
    """
    Keep only audio segments corresponding to non-filler words.
    Remove all other parts of the audio.
    """
    print("\n🔍 Keeping only non-filler word segments...")
    audio = AudioSegment.from_wav(audio_path)

    keep_intervals = []
    for w in words:
        word = w["word"].strip().lower()
        if word not in filler_words:
            start = max(0, w["start"] - buffer_sec)
            end = min(audio.duration_seconds, w["end"] + buffer_sec)
            keep_intervals.append((start, end))

    # Merge close intervals
    def merge_intervals(intervals, gap_threshold=0.1):
        if not intervals:
            return []
        intervals.sort()
        merged = [intervals[0]]
        for current in intervals[1:]:
            last = merged[-1]
            if current[0] <= last[1] + gap_threshold:
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)
        return merged

    merged_intervals = merge_intervals(keep_intervals)

    # Build clean audio
    clean_audio = AudioSegment.empty()
    for start, end in merged_intervals:
        segment = audio[start * 1000: end * 1000]
        segment = segment.fade_in(fade_ms).fade_out(fade_ms)
        clean_audio += segment

    return clean_audio


def mp3_to_wav(mp3_path, wav_path=None):
    """
    Convert an MP3 file to WAV format.

    Args:
        mp3_path (str): Path to the input MP3 file.
        wav_path (str, optional): Path to save the output WAV file.
            If None, saves to same folder with same name and .wav extension.

    Returns:
        str: Path to the saved WAV file.
    """
    audio = AudioSegment.from_mp3(mp3_path)
    
    if wav_path is None:
        base, _ = os.path.splitext(mp3_path)
        wav_path = base + ".wav"
    
    audio.export(wav_path, format="wav")
    return wav_path