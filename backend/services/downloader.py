"""
YouTube video downloader using yt-dlp.
Downloads videos from YouTube URLs for processing by the Hook Clipper pipeline.
"""

import subprocess
import logging
import re
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported URL patterns
YOUTUBE_PATTERNS = [
    r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
    r'(https?://)?(www\.)?youtu\.be/[\w-]+',
    r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
]


def validate_url(url: str) -> bool:
    """Validate that the URL is a supported YouTube URL."""
    for pattern in YOUTUBE_PATTERNS:
        if re.match(pattern, url.strip()):
            return True
    return False


def get_video_info(url: str) -> dict:
    """Fetch video metadata without downloading."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error(f"yt-dlp info failed: {result.stderr}")
            return {}

        info = json.loads(result.stdout)
        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown"),
        }
    except Exception as e:
        logger.warning(f"Failed to fetch video info: {e}")
        return {}


def download_youtube(url: str, output_dir: str) -> dict:
    """
    Download a YouTube video using yt-dlp.

    Args:
        url: YouTube video URL
        output_dir: Directory to save the downloaded video

    Returns:
        dict with keys: video_path, title, duration

    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If the download fails
    """
    # Validate URL
    if not validate_url(url):
        raise ValueError(f"Invalid or unsupported URL: {url}")

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Fetch video info first
    logger.info(f"Fetching video info for: {url}")
    info = get_video_info(url)
    title = info.get("title", "youtube_video")
    duration = info.get("duration", 0)

    # Sanitize title for filename
    safe_title = re.sub(r'[^\w\s-]', '', title)[:80].strip().replace(' ', '_')

    # Output template
    output_template = str(output_path / f"{safe_title}.%(ext)s")

    logger.info(f"Downloading: '{title}' ({duration}s) ...")

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                # Format: best video+audio up to 720p, merged as mp4
                "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "--merge-output-format", "mp4",
                # Output path
                "-o", output_template,
                # No playlist, just the single video
                "--no-playlist",
                # Overwrite if exists
                "--force-overwrites",
                # Quiet progress (we log ourselves)
                "--no-progress",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=600,  # 10 min timeout for large videos
        )

        if result.returncode != 0:
            logger.error(f"yt-dlp download failed: {result.stderr}")
            raise RuntimeError(f"Download failed: {result.stderr.strip()}")

    except subprocess.TimeoutExpired:
        raise RuntimeError("Download timed out (>10 minutes). Try a shorter video.")

    # Find the downloaded file
    downloaded_files = list(output_path.glob(f"{safe_title}.*"))
    mp4_files = [f for f in downloaded_files if f.suffix == ".mp4"]

    if not mp4_files:
        raise RuntimeError(f"Download completed but no .mp4 file found in {output_path}")

    video_path = str(mp4_files[0])
    logger.info(f"Download complete: {video_path}")

    return {
        "video_path": video_path,
        "title": title,
        "duration": duration,
    }
