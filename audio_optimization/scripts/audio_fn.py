import os
import uuid
import json
import whisper # type: ignore
import subprocess
import tempfile
from pathlib import Path
from pydub import AudioSegment # type: ignore
from df.enhance import enhance, init_df, load_audio # type: ignore
from utils import (
    generate_transcription_and_timestamps,
    save_transcript_text,
    save_word_timestamps,
    remove_non_word_regions,
    save_transcript_metadata
)

def denoise_audio(input_path):
    """
    Perform noise reduction on an input audio file using DeepFilterNet.

    Parameters:
    -----------
    input_path : str
        Path to the input audio file to be denoised.

    Returns:
    --------
    enhanced : torch.Tensor
        The denoised audio waveform tensor (1D).
    sample_rate : int
        The sample rate used for audio processing, as expected by the DeepFilterNet model.
    """
    model, df_state, _ = init_df()
    audio, _ = load_audio(input_path, sr=df_state.sr())
    enhanced = enhance(model, df_state, audio)
    return enhanced, df_state.sr()


def disfluency_removal(audio_seg, sr):
    """
    Removes disfluencies (filler words) from an AudioSegment.
    Saves transcript, timestamps, and UUID metadata.
    """
    model = whisper.load_model("turbo")
    filler_words = {"um", "uh", "ah", "erm", "mm", "hmm"}
    buffer_sec = 0.05
    fade_ms = 20

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_path = temp_wav.name
        audio_seg.export(temp_path, format="wav")

    try:
        full_text, words = generate_transcription_and_timestamps(model, temp_path)

        file_uuid = str(uuid.uuid4())
        output_dir = "output"
        transcript_path = os.path.join(output_dir, f"{file_uuid}.txt")
        word_ts_path = os.path.join(output_dir, f"{file_uuid}_timestamps.json")

        save_transcript_text(full_text, transcript_path)
        save_word_timestamps(words, word_ts_path)
        save_transcript_metadata(file_uuid, output_dir)

        cleaned_audio = remove_non_word_regions(temp_path, words, filler_words, buffer_sec, fade_ms)
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

