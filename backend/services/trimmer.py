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
            logger.error(f"Failed to trim clip {i + 1}: {e}")
            hook["clip_path"] = None
            hook["clip_filename"] = None
            hook["error"] = str(e)

    successful = [h for h in hooks if h.get("clip_path")]
    logger.info(f"Successfully trimmed {len(successful)}/{len(hooks)} clips")
    return hooks
