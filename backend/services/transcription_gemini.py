"""
Transcription service using Google Gemini 1.5 Flash (new google-genai SDK).
Sends audio directly to Gemini (multimodal) to get a timestamped transcript.
"""

import os
import logging
import json
import re
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")
        _client = genai.Client(api_key=api_key)
    return _client


def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe audio using Gemini 1.5 Flash multimodal input.

    Args:
        audio_path: Path to the audio file (mp3, wav, etc.)

    Returns:
        Dictionary with 'text', 'segments', 'words', and 'duration'
    """
    logger.info(f"[Gemini] Transcribing audio: {audio_path}")

    client = _get_client()

    # Upload file to Gemini Files API
    logger.info("[Gemini] Uploading audio file...")
    with open(audio_path, "rb") as f:
        uploaded = client.files.upload(
            file=f,
            config=types.UploadFileConfig(mime_type="audio/mpeg"),
        )
    logger.info(f"[Gemini] File uploaded: {uploaded.name}")

    prompt = """Please transcribe this audio file completely.
Return ONLY a valid JSON object in this exact format (no markdown, no extra text):
{
  "text": "Full transcript text here",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": "Segment text here"},
    {"start": 5.2, "end": 10.8, "text": "Next segment here"}
  ],
  "duration": 120.5
}

The segments should represent natural speech pauses or sentences.
Timestamps should be in seconds as floats.
duration should be the total length of the audio in seconds."""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            types.Part.from_uri(file_uri=uploaded.uri, mime_type="audio/mpeg"),
            prompt,
        ],
    )

    raw = response.text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"[Gemini] Failed to parse transcription JSON: {e}")
        logger.error(f"[Gemini] Raw response: {raw[:500]}")
        raise RuntimeError("Gemini returned invalid JSON for transcription")

    # Ensure required fields exist
    result.setdefault("text", "")
    result.setdefault("segments", [])
    result.setdefault("words", [])
    if "duration" not in result and result["segments"]:
        result["duration"] = result["segments"][-1]["end"]
    result.setdefault("duration", 0)

    # Clean up uploaded file
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass

    logger.info(
        f"[Gemini] Transcription complete: {len(result['segments'])} segments, {result['duration']:.1f}s"
    )
    return result
