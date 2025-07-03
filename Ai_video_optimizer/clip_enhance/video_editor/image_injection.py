# from moviepy import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
# import os

# def insert_image_segment(video_path, image_path, start_time, end_time, output_path):
#     video = VideoFileClip(video_path)

#     # Extract full audio once to preserve it across all segments
#     full_audio = video.audio

#     before = video.subclipped(0, start_time)
#     after = video.subclipped(end_time, video.duration)

#     # Image clip with video shape, correct duration, and matching fps
#     image_clip = (
#         ImageClip(image_path)
#         .with_duration(end_time - start_time)
#         .resized(video.size)
#         .with_fps(video.fps)
#     )

#     # Concatenate video parts (visually replaced)
#     final = concatenate_videoclips([before, image_clip, after])

#     # Attach original audio
#     final = final.with_audio(full_audio)

#     # Save output
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     final.write_videofile(output_path, codec="libx264", audio_codec="aac")

# def insert_multiple_images(video_path, image_segments, output_path):
#     """
#     Inserts multiple image overlays at specified times while preserving original audio.

#     Parameters:
#         video_path (str): Path to the input video.
#         image_segments (list): List of tuples (image_path, start_time, end_time).
#         output_path (str): Path to save the enhanced video.
#     """
#     video = VideoFileClip(video_path)
#     audio = video.audio

#     image_clips = []
#     for image_path, start_time, end_time in image_segments:
#         clip = (
#             ImageClip(image_path)
#             .set_start(start_time)
#             .with_duration(end_time - start_time)
#             .resized(video.size)
#             .with_fps(video.fps)
#         )
#         image_clips.append(clip)

#     final = CompositeVideoClip([video.without_audio()] + image_clips).set_audio(audio)

#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     final.write_videofile(output_path, codec="libx264", audio_codec="aac")


# if __name__ == "__main__":
#     insert_image_segment(
#         video_path="data/speech_podcast.mp4",
#         image_path="images/context_168_172.png",
#         start_time=168.0,
#         end_time=172.0,
#         output_path="output/speech_podcast-enhanced.mp4"
#     )
