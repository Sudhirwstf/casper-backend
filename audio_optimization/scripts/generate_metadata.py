import os
import json
from openai import OpenAI  # new SDK usage
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_transcript(uuid, output_dir="output"):
    path = os.path.join(output_dir, f"{uuid}.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Transcript file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_metadata(prompt_text, platform):
    if platform.lower() == "apple":
        platform_prompt = """
Generate a podcast title and description optimized for **Apple Podcasts**.
- Title: Clear, short, keyword-friendly.
- Description: Up to 4000 characters. Include a show summary, guest mentions (if any), social or contact info, and SEO-relevant keywords. Do not use markdown formatting.
Return a JSON with "title" and "description".
"""
    elif platform.lower() == "spotify":
        platform_prompt = """
Generate a podcast title and description optimized for **Spotify**.
- Title: Direct and creative, still keyword-aware.
- Description: Use an engaging tone. Clickable links are allowed. Emphasize emotional or narrative hooks for algorithmic discovery.
Return a JSON with "title" and "description".
"""
    else:
        platform_prompt = "Generate a JSON with a short podcast title and description."

    prompt = f"""{platform_prompt}

Transcript:
{prompt_text}

Return only JSON with keys: "title" and "description".
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except Exception:
        return {
            "title": "Untitled Podcast",
            "description": content
        }


def update_metadata_file(meta_path):
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    uuid = meta.get("transcript_uuid")
    if not uuid:
        print(f"⚠️ Skipping {meta_path} — No transcript_uuid found.")
        return

    transcript = load_transcript(uuid)

    print(f"🎧 Generating metadata for: {uuid}")
    apple = generate_metadata(transcript, "Apple Podcasts")
    spotify = generate_metadata(transcript, "Spotify")

    meta.update({
        "apple_podcast_title": apple["title"],
        "apple_podcast_desc": apple["description"],
        "spotify_title": spotify["title"],
        "spotify_desc": spotify["description"]
    })

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"✅ Updated metadata: {meta_path}")


def main(output_dir="output"):
    print(f"🔍 Scanning {output_dir} for transcript metadata...")

    for filename in os.listdir(output_dir):
        if filename.endswith("_meta.json"):
            meta_path = os.path.join(output_dir, filename)
            update_metadata_file(meta_path)


if __name__ == "__main__":
    main()
