from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.scene_manager import save_images
import os

def detect_scenes(video_path, threshold=30.0, downscale=2, show_info=False):
    """
    Detects scenes in a video using content-based detection.

    Args:
        video_path (str): Path to input video.
        threshold (float): Sensitivity for content change (lower = more scenes).
        downscale (int): Factor to downscale frames for faster processing.
        show_info (bool): If True, prints number of scenes and durations.

    Returns:
        List of (start_time, end_time) tuples in seconds.
    """
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))

    video_manager.set_downscale_factor(downscale)
    video_manager.start()

    scene_manager.detect_scenes(frame_source=video_manager)

    scene_list = scene_manager.get_scene_list()
    scenes = [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]

    video_manager.release()

    if show_info:
        print(f"[🎬] Detected {len(scenes)} scenes.")
        for i, (start, end) in enumerate(scenes[:5]):
            print(f"  Scene {i+1}: {start:.2f}s → {end:.2f}s")

    return scenes


# CLI Test
if __name__ == "__main__":
    import sys
    from pprint import pprint

    if len(sys.argv) < 2:
        print("Usage: python scene_detector.py <video_path>")
        exit(1)

    video_path = sys.argv[1]
    scenes = detect_scenes(video_path, show_info=True)
    pprint(scenes[:5])
