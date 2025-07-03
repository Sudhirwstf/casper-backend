import os
import json
import argparse
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def call_openai(prompt, max_tokens=300):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return ""

def generate_metadata(summary):
    prompt = f"""
You are a social media content strategist.

Based on this summary of an educational video:
\"\"\"{summary}\"\"\"

Generate a JSON object with platform-specific titles and tags for Instagram, LinkedIn, and YouTube. Keep it short, engaging, and relevant.

Return only a JSON object like this:
{{
  "instagram": {{
    "title": "...",
    "tags": ["...", "..."]
  }},
  "linkedin": {{
    "title": "...",
    "tags": ["...", "..."]
  }},
  "youtube": {{
    "title": "...",
    "tags": ["...", "..."]
  }}
}}
"""
    response = call_openai(prompt)
    try:
        return json.loads(response)
    except Exception as e:
        print(f"❌ Failed to parse OpenAI response as JSON: {e}")
        return {}

def update_session_json(session_id):
    path = os.path.join("output", f"session_{session_id}.json")
    if not os.path.exists(path):
        print(f"❌ Session file not found: {path}")
        return

    data = load_json(path)
    
    summary_path = os.path.join("temp", f"{session_id}_summary.txt")
    if not os.path.exists(summary_path):
        print("❌ Summary file not found. Did this session use Clip Enhance?")
        return

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = f.read().strip()

    metadata = generate_metadata(summary)
    if metadata:
        data["platforms"] = metadata
        save_json(data, path)
        print(f"✅ Platform metadata added to {path}")
    else:
        print("⚠️ No metadata generated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate titles/tags for each platform using OpenAI")
    parser.add_argument("session_id", help="Session UUID (e.g., 1234abcd...)")
    args = parser.parse_args()
    update_session_json(args.session_id)
