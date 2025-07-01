import os
import uuid
import json
import requests
import whisper # type: ignore
import subprocess
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment # type: ignore
# from df.enhance import enhance, init_df, load_audio # type: ignore
from tempfile import NamedTemporaryFile
from utils import (
    generate_transcription_and_timestamps,
    save_transcript_text,
    save_word_timestamps,
    remove_non_word_regions,
    save_transcript_metadata
)

load_dotenv()

ZROK_URL = os.getenv("ZROK_DENOISE_URL")

# def denoise_audio(input_path):
#     """
#     Perform noise reduction on an input audio file using DeepFilterNet.

#     Parameters:
#     -----------
#     input_path : str
#         Path to the input audio file to be denoised.

#     Returns:
#     --------
#     enhanced : torch.Tensor
#         The denoised audio waveform tensor (1D).
#     sample_rate : int
#         The sample rate used for audio processing, as expected by the DeepFilterNet model.
#     """
#     model, df_state, _ = init_df()
#     audio, _ = load_audio(input_path, sr=df_state.sr())
#     enhanced = enhance(model, df_state, audio)
#     return enhanced, df_state.sr()

def denoise_audio(input_path):
    """
    Denoise audio by sending it to the hosted DeepFilterNet API via FastAPI + Zrok.

    Parameters:
    -----------
    input_path : str
        Path to the input audio file to be denoised.

    Returns:
    --------
    output_path : str
        Path to the denoised audio file saved locally.
    sample_rate : int
        Sample rate of the denoised audio (default: 16000).
    """
    if not ZROK_URL:
        raise EnvironmentError("ZROK_DENOISE_URL is not set in environment variables.")

    print(f"📤 Uploading audio to DeepFilterNet API: {input_path}")
    with open(input_path, "rb") as f:
        files = {"file": (input_path, f, "audio/wav")}
        response = requests.post(ZROK_URL, files=files)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to denoise audio: {response.status_code} - {response.text}")

    with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(response.content)
        output_path = temp_file.name

    print(f"✅ Denoised audio saved to: {output_path}")
    return output_path, 16000


def disfluency_removal(audio_seg: AudioSegment, sr: int):
    """
    Removes disfluencies (filler words) from an AudioSegment.
    Saves transcript, timestamps, and UUID metadata.
    Falls back to original audio if transcription has no word-level timestamps.
    """
    filler_words = {"um", "uh", "ah", "erm", "mm", "hmm"}
    buffer_sec = 0.05
    fade_ms = 20

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_path = temp_wav.name
        audio_seg.export(temp_path, format="wav")

    try:
        print("🎙️ Transcribing to identify disfluencies...")
        full_text, words = generate_transcription_and_timestamps(temp_path)

        file_uuid = str(uuid.uuid4())
        output_dir = "output"
        transcript_path = os.path.join(output_dir, f"{file_uuid}.txt")
        word_ts_path = os.path.join(output_dir, f"{file_uuid}_timestamps.json")

        save_transcript_text(full_text, transcript_path)
        save_word_timestamps(words, word_ts_path)
        save_transcript_metadata(file_uuid, output_dir)

        if not words:
            print("⚠️ No words detected in transcript. Skipping disfluency removal.")
            return audio_seg

        cleaned_audio = remove_non_word_regions(temp_path, words, filler_words, buffer_sec, fade_ms)

        if len(cleaned_audio) == 0:
            print("⚠️ Disfluency removal resulted in empty audio. Using original instead.")
            return audio_seg

    finally:
        os.remove(temp_path)

    return cleaned_audio

def normalize_audio(audio_seg, output_path, apply_normalization=True):
    """
    Normalize and optionally compress an audio segment using ffmpeg filters.

    This function exports the given AudioSegment to a temporary WAV file,
    then applies audio compression and loudness normalization filters using ffmpeg,
    and saves the processed audio to the specified output path.

    Parameters:
    -----------
    audio_seg : AudioSegment
        The audio segment to be processed and normalized.
    output_path : str
        The file path where the normalized audio will be saved.
    apply_normalization : bool, optional (default=True)
        Whether to apply loudness normalization along with compression.
        If False, only compression is applied.

    Effects:
    --------
    - Applies dynamic range compression with threshold -30dB, ratio 6, attack 10ms, release 1000ms.
    - Applies loudness normalization to target integrated loudness of -16 LUFS,
      true peak of -1.5 dB, and loudness range of 11 LU.
    - Saves the processed audio at `output_path`.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as raw_file:
        audio_seg.export(raw_file.name, format="wav")

    compress_filter = "acompressor=threshold=-30dB:ratio=6:attack=10:release=1000"
    normalize_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"

    if apply_normalization:
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_file.name,
            "-af", f"{compress_filter},{normalize_filter}",
            output_path
        ], check=True)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_file.name,
            "-af", compress_filter,
            output_path
        ], check=True)

