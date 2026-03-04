"""
Transcription service using mlx-whisper (Apple Silicon optimized).
Converts audio to text with timestamps — runs 100% locally.

Model is configurable via .env:
  WHISPER_MODEL=mlx-community/whisper-large-v3-turbo   (default, best quality/speed)
  WHISPER_MODEL=mlx-community/whisper-medium-mlx        (faster, slightly less accurate)
  WHISPER_MODEL=mlx-community/whisper-small-mlx         (fastest, good for short clips)
"""

import os
import logging

logger = logging.getLogger(__name__)

# Model is read from env — can be changed without touching code
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")


def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe audio using mlx-whisper (Apple Silicon GPU-accelerated).

    Args:
        audio_path: Path to the audio file (mp3, wav, etc.)

    Returns:
        Dictionary with 'text', 'segments', 'words', and 'duration'
        — same format as openai and gemini transcription services.
    """
    logger.info(f"[mlx-whisper] Transcribing: {audio_path} with model: {WHISPER_MODEL}")

    try:
        import mlx_whisper
    except ImportError:
        raise RuntimeError(
            "mlx-whisper is not installed. Run: pip install mlx-whisper"
        )

    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=WHISPER_MODEL,
        word_timestamps=True,
    )

    # Parse segments into our standard format
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": float(seg.get("start", 0)),
            "end": float(seg.get("end", 0)),
            "text": seg.get("text", "").strip(),
        })

    # Parse word-level timestamps if available
    words = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            words.append({
                "word": w.get("word", "").strip(),
                "start": float(w.get("start", 0)),
                "end": float(w.get("end", 0)),
            })

    duration = segments[-1]["end"] if segments else 0.0

    output = {
        "text": result.get("text", ""),
        "segments": segments,
        "words": words,
        "duration": duration,
    }

    logger.info(
        f"[mlx-whisper] Done: {len(segments)} segments, {len(words)} words, {duration:.1f}s"
    )
    return output
