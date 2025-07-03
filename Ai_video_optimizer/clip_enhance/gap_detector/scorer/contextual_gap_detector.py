import os
import re
import json
import requests
from typing import List, Dict
from dotenv import load_dotenv

# === Load Environment ===
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("❌ GROQ_API_KEY not found in .env file")

# === Constants ===
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}
MODEL = "llama3-70b-8192"
BATCH_SIZE = 10

# === Scoring Functions ===
def build_batch_prompt(lines: List[str]) -> str:
    joined = "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))
    return f"""
You are helping enhance an educational video by identifying lines that are difficult to visualize or understand without a visual aid.

Instructions:
- Carefully read each line from the transcript.
- Assign a score from 0.0 to 1.0 for each line:
  - 1.0 = Definitely needs a visual explanation (abstract, technical, complex)
  - 0.0 = No visual needed at all (already vivid, obvious, or fully descriptive)
  - Use intermediate values like 0.1, 0.3, 0.7, etc. if visual support would be helpful but not essential.
- Think about how hard it is to grasp the idea without a picture, chart, diagram, or illustration.

Return only a JSON array of floats — one for each line, in order — like:
[0.0, 0.9, 0.4, 0.2]

Transcript Lines:
{joined}
"""


def get_batch_contextual_scores(lines: List[str]) -> List[float]:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an assistant that scores text lines for visual enhancement."},
            {"role": "user", "content": build_batch_prompt(lines)}
        ],
        "temperature": 0.2,
        "max_tokens": 2048,
    }
    try:
        response = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()

        match = re.search(r"\[(.*?)\]", content, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON array found in response.")
        raw_array = f"[{match.group(1)}]"
        scores = json.loads(raw_array)

        if not isinstance(scores, list) or not all(isinstance(s, (int, float)) for s in scores):
            raise ValueError("Response is not a valid list of numbers")
        return [round(float(score), 3) for score in scores]

    except Exception as e:
        print(f"[⚠️] Batch scoring failed: {e}")
        try:
            print(f"[🪵] Raw response: {response.text}")
        except:
            pass
        return [0.0 for _ in lines]

def score_transcript_chunks(
    transcript: List[Dict],
    batch_size: int = BATCH_SIZE,
    persist: bool = False,
    output_path: str = None
) -> List[Dict]:
    """
    Scores transcript chunks and optionally saves to disk.

    Returns the in-memory scored transcript.
    """
    scored = []
    for i in range(0, len(transcript), batch_size):
        batch = transcript[i:i + batch_size]
        lines = [chunk['text'] for chunk in batch]
        print(f"[📦] Scoring batch {i // batch_size + 1} with {len(lines)} lines...")
        scores = get_batch_contextual_scores(lines)
        for chunk, score in zip(batch, scores):
            print(f"[📚] '{chunk['text']}' => c_score: {score}")
            scored.append({**chunk, "c_score": score})

    if persist and output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scored, f, indent=2, ensure_ascii=False)
        print(f"[💾] Scored transcript saved to {output_path}")

    return scored
