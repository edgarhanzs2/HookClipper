"""
Video trimming service using FFmpeg.
Cuts clips from the source video at specified timestamps.
"""

import subprocess
import os
import logging

logger = logging.getLogger(__name__)


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format for FFmpeg."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def trim_clip(
    video_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
) -> str:
    """
    Trim a clip from a video file using FFmpeg.
    
    Args:
        video_path: Path to the source video file
        start_time: Start time in seconds
        end_time: End time in seconds
        output_path: Path for the output clip
        
    Returns:
        Path to the trimmed clip
    """
    start_ts = format_timestamp(start_time)
    end_ts = format_timestamp(end_time)

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-ss", start_ts,
        "-to", end_ts,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-y",  # Overwrite output
        output_path,
    ]

    logger.info(f"Trimming clip: {start_ts} -> {end_ts}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 min timeout per clip
        )
        if result.returncode != 0:
            logger.error(f"FFmpeg trim error: {result.stderr[-500:]}")
            raise RuntimeError(f"FFmpeg clip trimming failed")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install it with: brew install ffmpeg")

    if not os.path.exists(output_path):
        raise RuntimeError("Video trimming produced no output file")

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Clip saved: {output_path} ({file_size_mb:.1f}MB)")
    return output_path


def trim_all_clips(
    video_path: str,
    hooks: list[dict],
    output_dir: str,
    job_id: str,
) -> list[dict]:
    """
    Trim all detected hooks from the source video.
    
    Args:
        video_path: Path to the source video
        hooks: List of hook dicts with start_time and end_time
        output_dir: Directory to save clips
        job_id: Job identifier for naming
        
    Returns:
        Updated hooks list with clip_path added
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, hook in enumerate(hooks):
        clip_filename = f"{job_id}_clip_{i + 1}.mp4"
        clip_path = os.path.join(output_dir, clip_filename)

        try:
            trim_clip(
                video_path=video_path,
                start_time=hook["start_time"],
                end_time=hook["end_time"],
                output_path=clip_path,
            )
            hook["clip_path"] = clip_path
            hook["clip_filename"] = clip_filename
        except Exception as e:
            logger.error(f"Failed to trim clip {i + 1} [{hook.get('title', '?')}]: {e}")
            hook["clip_path"] = None
            hook["clip_filename"] = None
            hook["error"] = str(e)

    successful = [h for h in hooks if h.get("clip_path")]
    failed = [h for h in hooks if not h.get("clip_path")]
    logger.info(f"Successfully trimmed {len(successful)}/{len(hooks)} clips")
    if failed:
        for h in failed:
            logger.warning(f"Clip failed to trim: '{h.get('title', '?')}' — {h.get('error', 'unknown error')}")
    if len(successful) == 0 and len(hooks) > 0:
        errors = "; ".join(h.get('error', 'unknown') for h in failed)
        raise RuntimeError(f"All {len(hooks)} clip(s) failed to trim. Errors: {errors}")
    return hooks


def trim_and_render_vertical(
    video_path: str,
    start_time: float,
    end_time: float,
    face_data: dict,
    subtitle_path: str,
    output_path: str,
) -> str:
    """
    Full vertical render pipeline: trim → crop to 9:16 → burn in subtitles.

    Args:
        video_path: Path to the source video
        start_time: Clip start time in seconds
        end_time: Clip end time in seconds
        face_data: Output from face_tracker.track_faces()
        subtitle_path: Path to the .ass subtitle file
        output_path: Path for the final vertical clip

    Returns:
        Path to the rendered vertical clip
    """
    import tempfile

    # Step 1: Trim the clip from the source video
    temp_trimmed = tempfile.mktemp(suffix="_trimmed.mp4")
    try:
        logger.info(f"Vertical render: trimming {start_time:.1f}s - {end_time:.1f}s")
        trim_clip(video_path, start_time, end_time, temp_trimmed)

        # Step 2: Crop to vertical + burn in subtitles in one FFmpeg pass
        src_width = face_data["width"]
        src_height = face_data["height"]

        # Calculate 9:16 crop dimensions
        aspect_ratio = 9.0 / 16.0
        crop_h = src_height
        crop_w = int(crop_h * aspect_ratio)

        if crop_w > src_width:
            crop_w = src_width
            crop_h = int(crop_w / aspect_ratio)

        # Average face X position for stable crop
        coords = face_data.get("coords", [])
        valid_coords = [c for c in coords if c.get("center_x") is not None]
        if valid_coords:
            avg_face_x = sum(c["center_x"] for c in valid_coords) / len(valid_coords)
        else:
            avg_face_x = 0.5

        # Compute crop X offset
        cx_px = int(avg_face_x * src_width)
        crop_x = max(0, min(cx_px - crop_w // 2, src_width - crop_w))
        crop_y = max(0, (src_height - crop_h) // 2)

        # Build filter: crop → scale → subtitle burn-in
        vf_parts = [
            f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}",
            "scale=1080:1920",
        ]

        if subtitle_path and os.path.exists(subtitle_path):
            # Escape special characters in path for FFmpeg
            safe_sub_path = subtitle_path.replace("\\", "/").replace(":", "\\:")
            vf_parts.append(f"ass='{safe_sub_path}'")

        filter_str = ",".join(vf_parts)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = [
            "ffmpeg",
            "-i", temp_trimmed,
            "-vf", filter_str,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "fast",
            "-crf", "23",
            "-y",
            output_path,
        ]

        logger.info(f"Vertical render: crop + subtitles → {output_path}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg vertical render error: {result.stderr[-500:]}")
            raise RuntimeError("FFmpeg vertical render failed")

        if not os.path.exists(output_path):
            raise RuntimeError("Vertical render produced no output file")

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Vertical render complete: {output_path} ({file_size_mb:.1f}MB)")

        return output_path

    finally:
        # Cleanup temp file
        try:
            os.remove(temp_trimmed)
        except Exception:
            pass
