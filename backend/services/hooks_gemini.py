"""
Hook detection service using Google Gemini 1.5 Flash (new google-genai SDK).
Analyzes transcript to find the most engaging, viral-worthy segments.
"""

import os
import json
import logging
import re
from google import genai

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


PROMPT_TEMPLATE = """You are a world-class viral content producer who specializes in finding the most engaging,
scroll-stopping moments from long-form content. Your job is to analyze a video transcript and identify
the 3-5 best "hooks" — segments that would perform extremely well as standalone short-form clips on
TikTok, YouTube Shorts, or Instagram Reels.

A great hook has one or more of these qualities:
- Opens with a bold, controversial, or surprising statement
- Contains a strong emotional moment (humor, shock, inspiration)
- Poses a compelling question that demands an answer
- Delivers a powerful insight or "aha moment"
- Has a natural beginning and ending (doesn't cut mid-thought)

Each clip should be between 30 and 90 seconds long.

IMPORTANT: You must return timestamps that actually exist in the transcript. Do not invent timestamps.
Use the segment timestamps provided to find accurate start/end times.

Return ONLY a valid JSON array (no markdown, no extra text) with this exact format:
[
  {{
    "title": "Short catchy title for this hook (max 60 chars)",
    "start_time": 12.5,
    "end_time": 58.3,
    "transcript_snippet": "First 100 characters of what's being said...",
    "reason": "Why this would go viral (1 sentence)",
    "score": 85
  }}
]

The score should be 1-100 representing how likely this clip is to go viral.
Sort by score descending (best first).
Only return the JSON array, no other text.

Here is a video transcript with timestamps (total duration: {duration:.0f} seconds):

{transcript}

Find the 3-5 most engaging, viral-worthy hooks from this transcript.
Remember: each clip should be 30-90 seconds and use accurate timestamps from the transcript above."""


def detect_hooks(transcript_data: dict) -> list:
    """
    Analyze a transcript and find the most engaging hooks using Gemini 1.5 Flash.

    Args:
        transcript_data: Dictionary with 'text', 'segments', and 'duration'

    Returns:
        List of hook objects with title, timestamps, score, etc.
    """
    formatted_segments = []
    for seg in transcript_data.get("segments", []):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()
        formatted_segments.append(f"[{start:.1f}s - {end:.1f}s] {text}")

    transcript_with_timestamps = "\n".join(formatted_segments)
    total_duration = transcript_data.get("duration", 0)

    prompt = PROMPT_TEMPLATE.format(
        duration=total_duration,
        transcript=transcript_with_timestamps,
    )

    logger.info(f"[Gemini] Sending transcript ({len(formatted_segments)} segments) for hook detection")

    client = _get_client()
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )

    raw = response.text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    logger.info(f"[Gemini] Response received ({len(raw)} chars)")

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            hooks = parsed
        elif isinstance(parsed, dict):
            hooks = parsed.get("hooks", parsed.get("clips", parsed.get("results", [])))
            if not isinstance(hooks, list):
                hooks = [parsed]
        else:
            hooks = []
    except json.JSONDecodeError as e:
        logger.error(f"[Gemini] Failed to parse hook detection JSON: {e}")
        logger.error(f"[Gemini] Raw response: {raw[:500]}")
        raise RuntimeError("Gemini returned invalid JSON for hook detection")

    # Validate and clean up timestamps
    validated_hooks = []
    for hook in hooks:
        start = float(hook.get("start_time", 0))
        end = float(hook.get("end_time", 0))
        start = max(0.0, start)
        end = min(end, float(total_duration)) if total_duration > 0 else end

        if end - start < 15:
            continue
        if end - start > 120:
            end = start + 90

        validated_hooks.append({
            "title": hook.get("title", "Untitled Hook"),
            "start_time": round(start, 1),
            "end_time": round(end, 1),
            "duration": round(end - start, 1),
            "transcript_snippet": hook.get("transcript_snippet", ""),
            "reason": hook.get("reason", ""),
            "score": min(100, max(1, int(hook.get("score", 50)))),
        })

    validated_hooks.sort(key=lambda x: x["score"], reverse=True)
    logger.info(f"[Gemini] Found {len(validated_hooks)} valid hooks")
    return validated_hooks
