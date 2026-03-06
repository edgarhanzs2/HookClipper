"""
Face tracking service using OpenCV.
Detects and tracks the dominant face across video frames for smart vertical cropping.
Uses OpenCV's built-in Haar cascade classifier for reliable face detection.
"""

import logging
from collections import deque

import cv2

logger = logging.getLogger(__name__)

# Load Haar cascade for face detection (ships with OpenCV)
_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def _smooth_coordinates(coords: list[dict], window_size: int = 15) -> list[dict]:
    """
    Apply a moving-average filter to face coordinates to prevent jittery cropping.

    Args:
        coords: List of {frame, center_x, center_y} dicts (may have None values)
        window_size: Number of frames to average over

    Returns:
        Smoothed list of {frame, center_x, center_y} dicts
    """
    if not coords:
        return coords

    smoothed = []
    x_window = deque(maxlen=window_size)
    y_window = deque(maxlen=window_size)

    for c in coords:
        if c["center_x"] is not None and c["center_y"] is not None:
            x_window.append(c["center_x"])
            y_window.append(c["center_y"])

        avg_x = sum(x_window) / len(x_window) if x_window else 0.5
        avg_y = sum(y_window) / len(y_window) if y_window else 0.5

        smoothed.append({
            "frame": c["frame"],
            "center_x": avg_x,
            "center_y": avg_y,
        })

    return smoothed


def track_faces(video_path: str, sample_every_n: int = 5) -> dict:
    """
    Run face detection on a video and return smoothed face coordinates.

    Args:
        video_path: Path to the video file
        sample_every_n: Process every Nth frame (higher = faster, less precise)

    Returns:
        dict with keys:
            - coords: list of {frame, center_x, center_y} (normalized 0-1)
            - total_frames: total frame count
            - fps: frames per second
            - width: video width in pixels
            - height: video height in pixels
            - faces_found: number of frames where a face was detected
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    logger.info(f"Face tracking: {total_frames} frames, {fps:.1f}fps, {width}x{height}, sample every {sample_every_n}")

    # OpenCV Haar cascade face detector
    face_cascade = cv2.CascadeClassifier(_CASCADE_PATH)
    if face_cascade.empty():
        raise RuntimeError(f"Failed to load Haar cascade from: {_CASCADE_PATH}")

    raw_coords = []
    faces_found = 0
    frame_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % sample_every_n == 0:
            # Convert to grayscale for Haar cascade
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
            )

            if len(faces) > 0:
                # Pick the largest (most prominent) face
                best = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = best

                # Center of the bounding box (normalized 0-1)
                cx = (x + w / 2) / width
                cy = (y + h / 2) / height

                raw_coords.append({
                    "frame": frame_num,
                    "center_x": cx,
                    "center_y": cy,
                })
                faces_found += 1
            else:
                # No face detected — mark as None for interpolation
                raw_coords.append({
                    "frame": frame_num,
                    "center_x": None,
                    "center_y": None,
                })

        frame_num += 1

    cap.release()

    # Fill in missing frames by repeating the nearest detected coord
    # (for frames we skipped via sample_every_n)
    all_coords = []
    coord_idx = 0
    for f in range(total_frames):
        if coord_idx < len(raw_coords) - 1 and raw_coords[coord_idx + 1]["frame"] <= f:
            coord_idx += 1

        if coord_idx < len(raw_coords):
            all_coords.append({
                "frame": f,
                "center_x": raw_coords[coord_idx]["center_x"],
                "center_y": raw_coords[coord_idx]["center_y"],
            })
        else:
            all_coords.append({
                "frame": f,
                "center_x": 0.5,
                "center_y": 0.5,
            })

    # Smooth the coordinates
    smoothed = _smooth_coordinates(all_coords, window_size=15)

    logger.info(f"Face tracking complete: {faces_found}/{len(raw_coords)} sampled frames had faces")

    return {
        "coords": smoothed,
        "total_frames": total_frames,
        "fps": fps,
        "width": width,
        "height": height,
        "faces_found": faces_found,
    }
