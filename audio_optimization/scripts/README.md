# Audio Processing Pipeline

This project provides a complete audio processing pipeline that removes background noise, eliminates filler words (disfluencies), and normalizes loudness in speech audio files. It leverages DeepFilterNet for noise suppression, Whisper for transcription and disfluency removal, and FFmpeg for audio normalization.

---

## Features

- **Noise Reduction:** Uses DeepFilterNet neural network for high-quality denoising.
- **Disfluency Removal:** Removes filler words like "um", "uh", "ah" by leveraging Whisper’s transcription and word-level timestamps.
- **Loudness Normalization:** Applies compression and loudness normalization filters using FFmpeg to produce balanced audio volume.

---

## Setup Instructions

Follow these steps carefully to get the pipeline up and running:

### 1. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/yourusername/audio-processing-pipeline.git
cd audio-processing-pipeline
```

### 2. Create and Activate a Python Virtual Environment
Create a clean environment to avoid dependency conflicts:

```bash
python3 -m venv venv
```

Activate the environment:

On Linux/macOS:

```bash
source venv/bin/activate
```

On Windows (PowerShell):
```bash
.\venv\Scripts\Activate.ps1
```

On Windows (Command Prompt):

```bash
venv\Scripts\activate.bat
```

### 3. Install Required Python Packages
Run the following command to install all necessary packages listed in requirements.txt:

```bash
pip install -r requirements.txt
```
#### Running the Pipeline:
    1. Place your input audio file inside the data/ directory. Supported formats include .wav and .mp3.

    2. Run the main script to process the audio:

    ```bash
    python main.py
    ```
    3. After successful processing, the cleaned and normalized audio will be saved inside the output/ folder with a suffix _final.wav. For example, if your input file was interview.mp3, the output will be:

    ```bash
    output/interview_final.wav
    ```

### Directory Structure
```bash
audio-processing-pipeline/
│
├── data/                   # Place input audio files here
├── output/                 # Processed audio files are saved here
├── audio_fn.py             # Core audio processing functions
├── main.py                 # Main script to run the full pipeline
├── utils.py                # Utility functions (e.g. mp3 to wav conversion)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Notes
The pipeline currently supports mp3 and wav audio formats; files will be converted to WAV automatically if needed.

For best performance, use a GPU-enabled PyTorch environment.

The processing steps include:

Noise reduction with DeepFilterNet

Disfluency removal by Whisper transcription and audio editing

Loudness normalization with FFmpeg filters

### License
This project is licensed under the __ License.

### Acknowledgments
    DeepFilterNet

    OpenAI Whisper

    FFmpeg