"""
Transcription service using OpenAI Whisper API.
Converts audio to text with timestamps.
Designed to be swappable with Deepgram in the future.
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe audio using OpenAI Whisper API.
    
    Args:
        audio_path: Path to the audio file (mp3, wav, etc.)
        
    Returns:
        Dictionary with 'text' (full transcript) and 'segments' 
        (list of segments with start/end timestamps)
    """
    logger.info(f"Transcribing audio: {audio_path}")

    # Check file size — Whisper API limit is 25MB
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb > 25:
        logger.warning(f"Audio file is {file_size_mb:.1f}MB, may need chunking for Whisper (25MB limit)")
        # For MVP, we'll proceed and let the API error if too large
        # In production, implement chunking here

    with open(audio_path, "rb") as audio_file:
        response = _get_client().audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"],
        )

    # Parse response into our standard format
    segments = []
    if hasattr(response, "segments") and response.segments:
        for seg in response.segments:
            segments.append({
                "start": seg.get("start", seg.start if hasattr(seg, "start") else 0),
                "end": seg.get("end", seg.end if hasattr(seg, "end") else 0),
                "text": seg.get("text", seg.text if hasattr(seg, "text") else ""),
            })

    # Extract word-level timestamps if available
    words = []
    if hasattr(response, "words") and response.words:
        for w in response.words:
            words.append({
                "word": w.get("word", w.word if hasattr(w, "word") else ""),
                "start": w.get("start", w.start if hasattr(w, "start") else 0),
                "end": w.get("end", w.end if hasattr(w, "end") else 0),
            })

    result = {
        "text": response.text,
        "segments": segments,
        "words": words,
        "duration": segments[-1]["end"] if segments else 0,
    }

    logger.info(f"Transcription complete: {len(segments)} segments, {len(words)} words, {result['duration']:.1f}s")
    return result
