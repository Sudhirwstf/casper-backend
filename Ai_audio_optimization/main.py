# import os
# import argparse
# import tempfile
# import uuid
# import json

# import torchaudio  # type: ignore
# from pydub import AudioSegment  # type: ignore
# from dotenv import load_dotenv

# import cloudinary  # type: ignore
# import cloudinary.uploader  # type: ignore

# from utils import mp3_to_wav
# from audio_fn import denoise_audio, normalize_audio, disfluency_removal
# from generate_metadata import generate_metadata  # <- your function from earlier

# # Load .env and configure Cloudinary
# load_dotenv()

# cloudinary.config(
#     cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
#     api_key=os.getenv("CLOUDINARY_API_KEY"),
#     api_secret=os.getenv("CLOUDINARY_API_SECRET")
# )

# def process_audio(input_audio_path):
#     base_name = os.path.splitext(os.path.basename(input_audio_path))[0]
#     output_dir = "output"
#     os.makedirs(output_dir, exist_ok=True)
#     final_output_path = os.path.join(output_dir, f"{base_name}_final.wav")

#     # Step 0: Convert to WAV if needed
#     if not input_audio_path.lower().endswith(".wav"):
#         print(f"🎵 Converting '{input_audio_path}' to WAV format...")
#         wav_path = mp3_to_wav(input_audio_path)
#     else:
#         wav_path = input_audio_path

#     # Step 1: Denoising
#     print("\n=== Step 1: Denoising ===")
#     denoised_path, sr = denoise_audio(wav_path)

#     # Load denoised audio back into a waveform for torchaudio processing
#     waveform, sr = torchaudio.load(denoised_path)
#     if waveform.dim() == 1:
#         waveform = waveform.unsqueeze(0)
#     elif waveform.dim() == 3:
#         waveform = waveform[0]

#     with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav_file:
#         torchaudio.save(temp_wav_file.name, waveform, sample_rate=sr)
#         denoised_wav_path = temp_wav_file.name

#     # Step 2: Disfluency Removal
#     denoised_audio_segment = AudioSegment.from_wav(denoised_wav_path)
#     print("\n=== Step 2: Disfluency Removal ===")
#     cleaned_audio = disfluency_removal(denoised_audio_segment, sr)

#     # Step 3: Normalization
#     print("\n=== Step 3: Normalization ===")
#     normalize_audio(cleaned_audio, final_output_path)

#     print(f"\n🎉 Done! Final processed audio saved at: {final_output_path}")

#     # Step 4: Upload to Cloudinary
#     print("\n☁️ Uploading to Cloudinary...")
#     upload_result = cloudinary.uploader.upload_large(
#         final_output_path,
#         resource_type="video",  # audio = video for Cloudinary
#         folder="enhanced_audio"
#     )
#     cloud_url = upload_result["secure_url"]
#     cloudinary_uuid = str(uuid.uuid4())

#     # Step 5: Load transcript UUID from metadata
#     meta_path = next(
#         (os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith("_meta.json")),
#         None
#     )

#     if not meta_path:
#         print("❌ No metadata file found.")
#         return

#     with open(meta_path, "r", encoding="utf-8") as f:
#         meta = json.load(f)
#     transcript_uuid = meta.get("transcript_uuid")

#     if not transcript_uuid:
#         print("❌ transcript_uuid missing in meta file.")
#         return

#     transcript_path = os.path.join(output_dir, f"{transcript_uuid}.txt")
#     with open(transcript_path, "r", encoding="utf-8") as f:
#         transcript_text = f.read()

#     # Step 6: Generate Podcast Metadata
#     apple_meta = generate_metadata(transcript_text, platform="Apple Podcasts")
#     spotify_meta = generate_metadata(transcript_text, platform="Spotify")

#     # Step 7: Save full result JSON
#     result = {
#         f"enhanced_{base_name}": {
#             "uuid": cloudinary_uuid,
#             "url": cloud_url,
#             "transcript_uuid": transcript_uuid,
#             "apple_podcast_title": apple_meta.get("title"),
#             "apple_podcast_desc": apple_meta.get("description"),
#             "spotify_title": spotify_meta.get("title"),
#             "spotify_desc": spotify_meta.get("description")
#         }
#     }

#     json_output_path = os.path.join(output_dir, f"{base_name}_final_output.json")
#     with open(json_output_path, "w", encoding="utf-8") as f:
#         json.dump(result, f, indent=2)

#     print(f"\n✅ All done! Output saved to: {json_output_path}")
#     return result


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='Process and enhance audio file.')
#     parser.add_argument('input_path', type=str, help='Path to input audio file (WAV or MP3)')
#     args = parser.parse_args()
#     process_audio(args.input_path)


import os
import argparse
import tempfile
import uuid
import json

import torchaudio  # type: ignore
from pydub import AudioSegment  # type: ignore
from dotenv import load_dotenv

import cloudinary  # type: ignore
import cloudinary.uploader  # type: ignore

from utils import mp3_to_wav
from audio_fn import denoise_audio, normalize_audio, disfluency_removal
from generate_metadata import generate_metadata  # <- your function from earlier

# Load .env and configure Cloudinary
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def process_audio(input_audio_path):
    # 🔹 Step 0: Generate UUID and announce it
    file_uuid = str(uuid.uuid4())
    print(f"session started for UUID: {file_uuid}")

    base_name = os.path.splitext(os.path.basename(input_audio_path))[0]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    final_output_path = os.path.join(output_dir, f"{file_uuid}_final.wav")

    # Step 1: Convert to WAV if needed
    if not input_audio_path.lower().endswith(".wav"):
        print(f"🎵 Converting '{input_audio_path}' to WAV format...")
        wav_path = mp3_to_wav(input_audio_path)
    else:
        wav_path = input_audio_path

    # Step 2: Denoising
    print("\n=== Step 1: Denoising ===")
    denoised_path, sr = denoise_audio(wav_path)

    # Load denoised audio for torchaudio processing
    waveform, sr = torchaudio.load(denoised_path)
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    elif waveform.dim() == 3:
        waveform = waveform[0]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav_file:
        torchaudio.save(temp_wav_file.name, waveform, sample_rate=sr)
        denoised_wav_path = temp_wav_file.name

    # Step 3: Disfluency Removal
    denoised_audio_segment = AudioSegment.from_wav(denoised_wav_path)
    print("\n=== Step 2: Disfluency Removal ===")
    cleaned_audio = disfluency_removal(denoised_audio_segment, sr)

    # Step 4: Normalization
    print("\n=== Step 3: Normalization ===")
    normalize_audio(cleaned_audio, final_output_path)

    print(f"\n🎉 Done! Final processed audio saved at: {final_output_path}")

    # Step 5: Upload to Cloudinary
    print("\n☁️ Uploading to Cloudinary...")
    upload_result = cloudinary.uploader.upload_large(
        final_output_path,
        resource_type="video",  # audio is treated as video on Cloudinary
        folder="enhanced_audio"
    )
    cloud_url = upload_result["secure_url"]

    # Step 6: Load transcript UUID from metadata
    meta_path = next(
        (os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith("_meta.json")),
        None
    )

    if not meta_path:
        print("❌ No metadata file found.")
        return

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    transcript_uuid = meta.get("transcript_uuid")

    if not transcript_uuid:
        print("❌ transcript_uuid missing in meta file.")
        return

    transcript_path = os.path.join(output_dir, f"{transcript_uuid}.txt")
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    # Step 7: Generate Podcast Metadata
    apple_meta = generate_metadata(transcript_text, platform="Apple Podcasts")
    spotify_meta = generate_metadata(transcript_text, platform="Spotify")

    # Step 8: Save full result JSON using UUID as filename
    result = {
        f"enhanced_{file_uuid}": {
            "uuid": file_uuid,
            "url": cloud_url,
            "transcript_uuid": transcript_uuid,
            "apple_podcast_title": apple_meta.get("title"),
            "apple_podcast_desc": apple_meta.get("description"),
            "spotify_title": spotify_meta.get("title"),
            "spotify_desc": spotify_meta.get("description")
        }
    }

    json_output_path = os.path.join(output_dir, f"{file_uuid}_final_output.json")
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\n✅ All done! Output saved to: {json_output_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process and enhance audio file.')
    parser.add_argument('input_path', type=str, help='Path to input audio file (WAV or MP3)')
    args = parser.parse_args()
    process_audio(args.input_path)
