"""
Audio extraction service using FFmpeg.
Extracts audio track from video files for transcription.
"""

import subprocess
import os
import logging

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_dir: str) -> str:
    """
    Extract audio from a video file using FFmpeg.
    
    Args:
        video_path: Path to the input video file
        output_dir: Directory to save the extracted audio
        
    Returns:
        Path to the extracted audio file (MP3)
    """
    audio_filename = os.path.splitext(os.path.basename(video_path))[0] + ".mp3"
    audio_path = os.path.join(output_dir, audio_filename)

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        "-y",  # Overwrite output
        audio_path,
    ]

    logger.info(f"Extracting audio: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr[-500:]}")
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg not found. Install it with: brew install ffmpeg"
        )

    if not os.path.exists(audio_path):
        raise RuntimeError("Audio extraction produced no output file")

    logger.info(f"Audio extracted to: {audio_path}")
    return audio_path
