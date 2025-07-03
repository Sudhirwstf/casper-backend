import os
import json
import requests #type: ignore
from openai import OpenAI #type: ignore
from dotenv import load_dotenv #type: ignore

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_image_prompt(summary, gap_context):
    prompt = f"""
You are helping enhance an educational video by generating image prompts that clearly visualize what the speaker is discussing during visually stagnant segments.

Video Summary:
"{summary}"

Transcript Segment (spoken content):
"{gap_context}"

Your task is to write a vivid, realistic, and coherent visual scene that directly illustrates the topic or key idea being discussed in this segment. The image should help a viewer understand or visualize what the speaker is talking about — making abstract ideas more concrete or showcasing real-world examples.

The description must:
- Clearly reflect the content of the transcript segment
- Use realistic objects, environments, diagrams, or scenes that would aid in understanding
- Be suitable for a text-to-image model like gpt-image-1

Avoid:
- Mentioning specific real people, names, or brands
- Abstract or intangible concepts that cannot be visualized
- Disturbing, violent, or medically graphic content

Write the image description as a single clear sentence. Return only the image description.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_image_from_prompt(prompt):
    print(f"🎨 Generating image for prompt: {prompt}")
    try:
        response = client.images.generate(
            model="gpt-image-1",  # Correct model name for OpenAI's latest image generation model
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="medium"
            # No response_format parameter - gpt-image-1 returns b64_json by default
        )
        # gpt-image-1 returns b64_json by default
        b64_image = response.data[0].b64_json
        return b64_image
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return None

def save_image_from_b64(b64_data, filename):
    try:
        import base64
        print(f"💾 Saving base64 image to: {filename}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Decode base64 and save
        image_data = base64.b64decode(b64_data)
        with open(filename, 'wb') as f:
            f.write(image_data)
        print(f"💾 Saved image to {filename} ({len(image_data)} bytes)")
        return True
    except Exception as e:
        print(f"❌ Failed to save base64 image: {e}")
        return False
    
def generate_images_for_gaps(gap_contexts, summary, save_to_disk=True, output_dir="images"):
    os.makedirs(output_dir, exist_ok=True)
    outputs = []

    for i, gap in enumerate(gap_contexts):
        context = gap.get("context", "").strip()
        if not context:
            continue

        prompt = generate_image_prompt(summary, context)
        print(f"📝 Generated prompt: {prompt}")
        
        b64_image = generate_image_from_prompt(prompt)
        print(f"🖼️ Generated base64 image: {'✅ Success' if b64_image else '❌ Failed'}")

        image_path = os.path.join(output_dir, f"gap_{i}.png")
        saved = False
        if b64_image and save_to_disk:
            saved = save_image_from_b64(b64_image, image_path)

        if not saved:
            print(f"⚠️ Skipping segment {i} due to image generation or saving failure.")
            continue

        outputs.append({
            "start": gap["start"],
            "end": gap["end"],
            "prompt": prompt,
            "image_b64": b64_image,
            "image_path": image_path
        })

    # ✅ Save alignment JSON to temp directory
    aligned_data = [
        {
            "start": item["start"],
            "end": item["end"],
            "prompt": item["prompt"],
            "image_path": item["image_path"]
        }
        for item in outputs
    ]
    os.makedirs("temp", exist_ok=True)
    aligned_json_path = "temp/image_prompt_segments.json"
    with open(aligned_json_path, "w", encoding="utf-8") as f:
        json.dump(aligned_data, f, indent=2)
    print(f"📁 Alignment JSON saved to: {aligned_json_path}")

    return outputs

# def generate_images_for_gaps(gap_contexts, summary, save_to_disk=True, output_dir="images"):
#     os.makedirs(output_dir, exist_ok=True)
#     outputs = []

#     for i, gap in enumerate(gap_contexts):
#         context = gap.get("context", "").strip()
#         if not context:
#             continue

#         prompt = generate_image_prompt(summary, context)
#         print(f"📝 Generated prompt: {prompt}")
        
#         b64_image = generate_image_from_prompt(prompt)
#         print(f"🖼️ Generated base64 image: {'✅ Success' if b64_image else '❌ Failed'}")

#         image_path = os.path.join(output_dir, f"gap_{i}.png")
#         saved = False
#         if b64_image and save_to_disk:
#             saved = save_image_from_b64(b64_image, image_path)

#         if not saved:
#             print(f"⚠️ Skipping segment {i} due to image generation or saving failure.")
#             continue

#         outputs.append({
#             "start": gap["start"],
#             "end": gap["end"],
#             "prompt": prompt,
#             "image_b64": b64_image,  # Store base64 data instead of URL
#             "image_path": image_path
#         })

#     return outputs
