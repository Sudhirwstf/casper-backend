# from dotenv import load_dotenv
# load_dotenv()

# import json
# import os
# import re
# from openai import OpenAI

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def score_transcript(transcript: list[dict], batch_size=80) -> list[float]:
#     """
#     Scores transcript segments in batches using OpenAI API (0–10 per segment),
#     now using a structured JSON array for accurate parsing.
#     """
#     scores = []

#     for i in range(0, len(transcript), batch_size):
#         batch = transcript[i:i + batch_size]
#         lines = [seg["text"].strip() for seg in batch if seg["text"].strip()]
#         prompt_text = "\n".join([f"{j + 1}. {line}" for j, line in enumerate(lines)])

#         prompt = (
#             "You are a video editor AI. Rate each of the following transcript segments from 0 to 10 "
#             "based ONLY on how emotionally engaging and informative they are.\n"
#             "Respond with a JSON array of numbers, where each number corresponds to each line.\n\n"
#             f"{prompt_text}\n\n"
#             "JSON:"
#         )

#         try:
#             response = client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.3,
#                 max_tokens=1500
#             )

#             content = response.choices[0].message.content.strip()
#             print(f"📩 Raw model output (batch {i}-{i+len(lines)}):\n{content[:200]}...")

#             # Parse only the JSON array
#             match = re.search(r"\[.*?\]", content, re.DOTALL)
#             if match:
#                 parsed = json.loads(match.group(0))
#                 if len(parsed) != len(batch):
#                     print(f"⚠️ Expected {len(batch)} scores, got {len(parsed)}. Padding with 0.0s.")
#                     parsed += [0.0] * (len(batch) - len(parsed))
#                 scores.extend([float(s) for s in parsed[:len(batch)]])
#             else:
#                 print("⚠️ No valid JSON array found. Defaulting batch to 0.0s.")
#                 scores.extend([0.0] * len(batch))

#         except Exception as e:
#             print(f"❌ Error during OpenAI call: {e}")
#             scores.extend([0.0] * len(batch))

#     return scores



# def map_context_scores_to_scenes(
#     scenes: list[tuple[float, float]],
#     transcript: list[dict],
#     context_scores: list[float],
#     visual_scores: list[float],
#     alpha: float = 0.5
# ) -> list[dict]:
#     """
#     Maps context scores from transcript segments to scenes based on overlap,
#     and blends them with visual diversity scores.
#     """
#     processed_transcript = [
#         {
#             "start": float(seg["start"]),
#             "end": float(seg["end"]),
#             "score": context_scores[i]
#         }
#         for i, seg in enumerate(transcript)
#     ]

#     scored_scenes = []

#     for i, (scene_start, scene_end) in enumerate(scenes):
#         scene_start = float(scene_start)
#         scene_end = float(scene_end)

#         overlapping_scores = [
#             seg["score"]
#             for seg in processed_transcript
#             if seg["start"] < scene_end and seg["end"] > scene_start
#         ]

#         context_score = sum(overlapping_scores) / len(overlapping_scores) if overlapping_scores else 0.0
#         raw_visual_score = visual_scores[i]
#         visual_score = raw_visual_score["score"] if isinstance(raw_visual_score, dict) else float(raw_visual_score)

#         final_score = alpha * context_score + (1 - alpha) * visual_score

#         scored_scenes.append({
#             "start": scene_start,
#             "end": scene_end,
#             "score": final_score
#         })

#     return sorted(scored_scenes, key=lambda x: x["score"], reverse=True)

from dotenv import load_dotenv
load_dotenv()

import json
import os
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def score_transcript(transcript: list[dict], batch_size=80) -> list[float]:
    """
    Scores transcript segments in batches using OpenAI API (0–10 per segment),
    now using robust JSON parsing to handle malformed output.
    """
    scores = []

    for i in range(0, len(transcript), batch_size):
        batch = transcript[i:i + batch_size]
        lines = [seg["text"].strip() for seg in batch if seg["text"].strip()]
        prompt_text = "\n".join([f"{j + 1}. {line}" for j, line in enumerate(lines)])

        prompt = (
            "You are a video editor AI. Rate each of the following transcript segments from 0 to 10 "
            "based ONLY on how emotionally engaging and informative they are.\n"
            "Respond with a **pure JSON array of numbers only**, without any explanation, markdown, or additional text.\n\n"
            f"{prompt_text}\n\n"
            "JSON:"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()
            print(f"📩 Raw model output (batch {i}-{i + len(lines)}):\n{content[:200]}...")

            # Try extracting all JSON arrays and use the longest one
            matches = re.findall(r"\[.*?\]", content, re.DOTALL)
            if matches:
                json_array = max(matches, key=len)
                try:
                    parsed = json.loads(json_array)
                    if len(parsed) != len(batch):
                        print(f"⚠️ Expected {len(batch)} scores, got {len(parsed)}. Padding with 0.0s.")
                        parsed += [0.0] * (len(batch) - len(parsed))
                    scores.extend([float(s) for s in parsed[:len(batch)]])
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to decode JSON: {e}. Defaulting batch to 0.0s.")
                    scores.extend([0.0] * len(batch))
            else:
                print("⚠️ No valid JSON array found. Defaulting batch to 0.0s.")
                scores.extend([0.0] * len(batch))

        except Exception as e:
            print(f"❌ Error during OpenAI call: {e}")
            scores.extend([0.0] * len(batch))

    return scores


def map_context_scores_to_scenes(
    scenes: list[tuple[float, float]],
    transcript: list[dict],
    context_scores: list[float],
    visual_scores: list[float],
    alpha: float = 0.5
) -> list[dict]:
    """
    Maps context scores from transcript segments to scenes based on overlap,
    and blends them with visual diversity scores.
    """
    processed_transcript = [
        {
            "start": float(seg["start"]),
            "end": float(seg["end"]),
            "score": context_scores[i]
        }
        for i, seg in enumerate(transcript)
    ]

    scored_scenes = []

    for i, (scene_start, scene_end) in enumerate(scenes):
        scene_start = float(scene_start)
        scene_end = float(scene_end)

        overlapping_scores = [
            seg["score"]
            for seg in processed_transcript
            if seg["start"] < scene_end and seg["end"] > scene_start
        ]

        context_score = sum(overlapping_scores) / len(overlapping_scores) if overlapping_scores else 0.0
        raw_visual_score = visual_scores[i]
        visual_score = raw_visual_score["score"] if isinstance(raw_visual_score, dict) else float(raw_visual_score)

        final_score = alpha * context_score + (1 - alpha) * visual_score

        scored_scenes.append({
            "start": scene_start,
            "end": scene_end,
            "score": final_score
        })

    return sorted(scored_scenes, key=lambda x: x["score"], reverse=True)
