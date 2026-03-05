"""
Vertical crop engine using FFmpeg.
Crops 16:9 video to 9:16 portrait format using face tracking coordinates.
"""

import subprocess
import os
import logging
import json
import tempfile

logger = logging.getLogger(__name__)


def _compute_crop_x(face_center_x: float, src_width: int, crop_width: int) -> int:
    """
    Compute the X offset for cropping, centered on the face.
    Clamps so the crop window stays within the frame.
    """
    # Face center in pixels
    cx_px = int(face_center_x * src_width)

    # Crop window left edge
    x = cx_px - crop_width // 2

    # Clamp to frame bounds
    x = max(0, min(x, src_width - crop_width))
    return x


def crop_to_vertical(
    video_path: str,
    face_data: dict,
    output_path: str,
    target_width: int = 1080,
    target_height: int = 1920,
) -> str:
    """
    Crop a 16:9 (or any landscape) video to 9:16 vertical using face tracking data.

    For efficiency, we use a single static crop position based on the average
    face position across all frames. This avoids complex per-frame scripting
    and produces smooth, professional results.

    Args:
        video_path: Path to the source video
        face_data: Output from face_tracker.track_faces()
        output_path: Path for the cropped output video
        target_width: Output width (default 1080)
        target_height: Output height (default 1920)

    Returns:
        Path to the cropped video
    """
    src_width = face_data["width"]
    src_height = face_data["height"]
    coords = face_data.get("coords", [])

    # Calculate the crop dimensions from the source video
    # We want a 9:16 aspect ratio crop from the source
    aspect_ratio = 9.0 / 16.0

    # Crop height = full source height, crop width = height * 9/16
    crop_h = src_height
    crop_w = int(crop_h * aspect_ratio)

    # If the source is narrower than our desired crop, use full width instead
    if crop_w > src_width:
        crop_w = src_width
        crop_h = int(crop_w / aspect_ratio)

    logger.info(f"Crop window: {crop_w}x{crop_h} from {src_width}x{src_height}")

    # Compute average face X position for a stable crop
    valid_coords = [c for c in coords if c["center_x"] is not None]
    if valid_coords:
        avg_face_x = sum(c["center_x"] for c in valid_coords) / len(valid_coords)
    else:
        avg_face_x = 0.5  # Center fallback

    crop_x = _compute_crop_x(avg_face_x, src_width, crop_w)

    # Center Y crop (for landscape->portrait, usually we want the full height)
    crop_y = max(0, (src_height - crop_h) // 2)

    logger.info(f"Crop position: x={crop_x}, y={crop_y}, face_avg_x={avg_face_x:.3f}")

    # Build FFmpeg command: crop then scale to target resolution
    filter_str = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={target_width}:{target_height}"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", filter_str,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-y",
        output_path,
    ]

    logger.info(f"Running vertical crop: {' '.join(cmd[:6])}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )
        if result.returncode != 0:
            logger.error(f"FFmpeg crop error: {result.stderr[-500:]}")
            raise RuntimeError("FFmpeg vertical crop failed")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install it with: brew install ffmpeg")

    if not os.path.exists(output_path):
        raise RuntimeError("Vertical crop produced no output file")

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Vertical crop saved: {output_path} ({file_size_mb:.1f}MB)")

    return output_path


def center_crop_vertical(
    video_path: str,
    output_path: str,
    target_width: int = 1080,
    target_height: int = 1920,
) -> str:
    """
    Simple center crop to vertical without face tracking.
    Fallback when face detection is not needed or fails.
    """
    # Probe source dimensions
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", video_path,
    ]

    try:
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
        streams = json.loads(probe_result.stdout)
        video_stream = next(s for s in streams["streams"] if s["codec_type"] == "video")
        src_width = int(video_stream["width"])
        src_height = int(video_stream["height"])
    except Exception:
        # Default to 1920x1080 if probe fails
        src_width = 1920
        src_height = 1080

    aspect_ratio = 9.0 / 16.0
    crop_h = src_height
    crop_w = int(crop_h * aspect_ratio)

    if crop_w > src_width:
        crop_w = src_width
        crop_h = int(crop_w / aspect_ratio)

    crop_x = (src_width - crop_w) // 2
    crop_y = (src_height - crop_h) // 2

    filter_str = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={target_width}:{target_height}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", filter_str,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-y",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError("FFmpeg center crop failed")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install it with: brew install ffmpeg")

    if not os.path.exists(output_path):
        raise RuntimeError("Center crop produced no output file")

    return output_path
