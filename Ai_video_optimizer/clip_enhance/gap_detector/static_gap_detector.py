import os
import cv2
import numpy as np


def detect_static_segments(video_path, threshold_seconds=3.0, frame_sample_rate=1, similarity_threshold=0.99):
    """
    Detects static visual gaps where frames do not change significantly.

    Args:
        video_path (str): Path to input video.
        threshold_seconds (float): Minimum duration for a static segment.
        frame_sample_rate (int): Analyze every Nth frame (1 = every frame).
        similarity_threshold (float): Minimum similarity between frames to consider as static.

    Returns:
        List of (start_time, end_time) tuples for static segments.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * frame_sample_rate)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    prev_frame = None
    static_start = None
    static_segments = []

    for i in range(0, total_frames, frame_interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (320, 240))  # speed up comparison

        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, gray)
            non_zero_count = np.count_nonzero(diff)
            similarity = 1 - (non_zero_count / diff.size)

            time_in_seconds = i / fps
            # print(f"Frame {i}: similarity={similarity:.4f}")  # Uncomment for debugging

            if similarity >= similarity_threshold:
                if static_start is None:
                    static_start = time_in_seconds
            else:
                if static_start is not None:
                    duration = time_in_seconds - static_start
                    if duration >= threshold_seconds:
                        static_segments.append((static_start, time_in_seconds))
                    static_start = None

        prev_frame = gray

    # Handle if video ends with a static segment
    if static_start is not None:
        end_time = total_frames / fps
        if end_time - static_start >= threshold_seconds:
            static_segments.append((static_start, end_time))

    cap.release()
    return static_segments


if __name__ == "__main__":
    test_video = "data/speech_podcast.mp4"
    static_gaps = detect_static_segments(
        test_video,
        threshold_seconds=4.0,
        frame_sample_rate=1,
        similarity_threshold=0.80  # More relaxed
    )
    for start, end in static_gaps:
        print(f"[🪄] Static segment: {start:.2f}s to {end:.2f}s")
