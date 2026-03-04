"""
Hook detection service using Ollama (local LLM).
Analyzes transcript to find the most engaging, viral-worthy segments.
Runs 100% locally — no API keys needed.

Model is configurable via .env:
  OLLAMA_MODEL=llama3.1     (default, best quality/speed balance)
  OLLAMA_MODEL=qwen2.5      (great structured reasoning / JSON output)
  OLLAMA_MODEL=gemma2       (high intelligence, slightly more RAM)
  OLLAMA_MODEL=phi3.5       (fastest, lowest RAM)

Ollama base URL is also configurable:
  OLLAMA_BASE_URL=http://localhost:11434  (default)
"""

import os
import json
import logging
import re
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# Configurable via .env
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

SYSTEM_PROMPT = """You are a viral content producer. Analyze the video transcript and identify the 3-5 best hook segments for TikTok/Shorts/Reels.

IMPORTANT RULES:
1. Each hook MUST be 30 to 90 seconds long. NEVER use a single transcript line's timestamps.
2. To choose a hook: pick a START line where something interesting begins, then find an END line approximately 30-60 seconds later in the transcript. Use the start of the first line and the end of the last line.
3. Example: if you see '[120.0s - 123.5s] Something bold happens' and '[162.0s - 165.0s] And here it resolves', then start_time=120.0 and end_time=165.0 (a 45-second clip).
4. DO NOT copy a single line's timestamps — that would only be 2-4 seconds, which is too short.

A great hook:
- Opens with a bold or surprising statement
- Contains strong emotion (humor, shock, inspiration)
- Has a natural beginning and ending
- Is 30-90 seconds long

You MUST respond with valid JSON in this EXACT format:
{
  "hooks": [
    {
      "title": "Catchy title max 60 chars",
      "start_time": 120.0,
      "end_time": 165.0,
      "transcript_snippet": "First 100 chars of the spoken text...",
      "reason": "One sentence on why this would go viral.",
      "score": 85
    }
  ]
}

start_time and end_time MUST differ by 30-90 seconds. No shorter clips."""


def _ts_to_seconds(ts_str: str) -> float:
    """
    Convert a timestamp string to seconds.
    Handles formats: '636.2', '636.2s', '10:30', '1:10:30'
    """
    ts_str = ts_str.strip().rstrip('s')
    if ':' in ts_str:
        parts = ts_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(ts_str)


def _find_best_timestamp_pair(text: str) -> tuple[float, float] | None:
    """
    Scan text for ALL timestamp pairs and return the one with the widest span.
    This handles Ollama putting timestamps anywhere in the section, not just on the title line.
    Formats handled: seconds (636.2s), MM:SS (10:30), HH:MM:SS (1:10:30)
    """
    # Match pairs like: 636.2s – 700.0s  OR  10:30 – 11:15  OR  10:30 to 11:15
    ts_pattern = re.compile(
        r'([\d]+(?::\d{2})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*s?\s*'   # start
        r'[–\-—to]+\s*'                                            # separator  
        r'([\d]+(?::\d{2})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*s?',      # end
        re.IGNORECASE,
    )
    best = None
    best_span = -1
    for m in ts_pattern.finditer(text):
        try:
            start = _ts_to_seconds(m.group(1))
            end = _ts_to_seconds(m.group(2))
            span = end - start
            if span > best_span:
                best_span = span
                best = (start, end)
        except (ValueError, IndexError):
            continue
    return best


def _parse_markdown_hooks(raw: str, total_duration: float) -> list:
    """
    Fallback parser for when Ollama returns a markdown numbered list instead of JSON.
    Scans the entire section for any timestamp pairs (not just the title line),
    and picks the widest span found to handle varied Ollama output formats.
    """
    hooks = []

    # Log first 800 chars of raw response so we can diagnose format issues
    logger.debug(f"[Ollama] Markdown fallback raw (first 800 chars):\n{raw[:800]}")

    # Title extraction: numbered item with optional bold/quoted title
    title_pattern = re.compile(
        r'^\d+[\.\)]\s+(?:\*{1,2})?["\']?(.*?)["\']?(?:\*{1,2})?\s*$',
        re.MULTILINE,
    )

    # Split into numbered sections
    sections = re.split(r'\n(?=\d+[\.\)])', raw)
    scores = [90, 80, 70, 60, 50]

    for i, section in enumerate(sections):
        # Find the best (widest) timestamp pair anywhere in this section
        pair = _find_best_timestamp_pair(section)
        if not pair:
            logger.debug(f"[Ollama] Section {i+1}: no timestamp pair found, skipping")
            continue

        start, end = pair

        # Extract title from first line
        first_line = section.strip().split('\n')[0]
        title_match = title_pattern.match(first_line.strip())
        title = title_match.group(1).strip().strip('"\'*') if title_match else first_line.strip()[:60]

        # Get reason from lines after title
        lines = section.strip().split('\n')
        reason_lines = [l.strip() for l in lines[1:] if l.strip() and not re.search(r'\d+s?\s*[–\-—]', l)]
        reason = reason_lines[0][:200] if reason_lines else "Engaging moment detected."

        logger.info(f"[Ollama] Markdown hook {i+1}: '{title[:40]}' {start:.1f}s–{end:.1f}s (span={end-start:.1f}s)")

        hooks.append({
            "title": title[:60],
            "start_time": start,
            "end_time": end,
            "transcript_snippet": title[:100],
            "reason": reason,
            "score": scores[i] if i < len(scores) else 50,
        })

    return hooks


def detect_hooks(transcript_data: dict) -> list:
    """
    Analyze a transcript and find the most engaging hooks using a local Ollama LLM.

    Args:
        transcript_data: Dictionary with 'text', 'segments', and 'duration'

    Returns:
        List of hook objects with title, timestamps, score, etc.
    """
    # Build formatted transcript with timestamps
    formatted_segments = []
    for seg in transcript_data.get("segments", []):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()
        formatted_segments.append(f"[{start:.1f}s - {end:.1f}s] {text}")

    transcript_with_timestamps = "\n".join(formatted_segments)
    total_duration = transcript_data.get("duration", 0)

    # Truncate transcript to avoid overflowing the local model's context window.
    # llama3.1 locally supports ~8k tokens; a 338-segment transcript can be 10k+ chars.
    # We sample evenly across the video so we see hooks from beginning, middle, and end.
    MAX_TRANSCRIPT_CHARS = int(os.getenv("OLLAMA_MAX_TRANSCRIPT_CHARS", "4000"))
    if len(transcript_with_timestamps) > MAX_TRANSCRIPT_CHARS:
        # Even sampling: pick segments spread across the whole video
        step = max(1, len(formatted_segments) // 60)  # aim for ~60 segments
        sampled = formatted_segments[::step]
        transcript_with_timestamps = "\n".join(sampled)
        # If still too long, hard truncate with ellipsis
        if len(transcript_with_timestamps) > MAX_TRANSCRIPT_CHARS:
            transcript_with_timestamps = transcript_with_timestamps[:MAX_TRANSCRIPT_CHARS] + "\n... [transcript truncated]"
        logger.info(
            f"[Ollama] Transcript truncated: {len(formatted_segments)} segments → "
            f"{len(sampled)} sampled ({len(transcript_with_timestamps)} chars)"
        )

    user_prompt = f"""Here is a video transcript with timestamps (total duration: {total_duration:.0f} seconds):

{transcript_with_timestamps}

Find the 3-5 most engaging, viral-worthy hooks from this transcript.
Remember: each clip should be 30-90 seconds and use accurate timestamps from the transcript above."""

    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

    logger.info(
        f"[Ollama] Sending transcript ({len(formatted_segments)} segments) "
        f"to {OLLAMA_MODEL} for hook detection"
    )

    # Call Ollama HTTP API with format=json to force structured output
    # Note: format=json requires a root JSON object, not a bare array.
    # The system prompt uses {"hooks": [...]} wrapper accordingly.
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.3,
            "num_predict": 2000,
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            response_body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
            f"Is Ollama running? Start it with: ollama serve\nError: {e}"
        )

    raw = response_body.get("response", "").strip()
    logger.info(f"[Ollama] Raw response ({len(raw)} chars): {raw[:300]}")

    # Strip markdown code fences if model wraps in ```json ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)

    logger.info(f"[Ollama] Response received ({len(raw)} chars)")

    # --- Strategy 1: extract JSON array directly ---
    hooks = None
    json_str = raw
    array_match = re.search(r"\[.*\]", raw, flags=re.DOTALL)
    if array_match:
        json_str = array_match.group(0)

    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            hooks = parsed
        elif isinstance(parsed, dict):
            hooks = parsed.get("hooks", parsed.get("clips", parsed.get("results", [])))
            if not isinstance(hooks, list):
                hooks = [parsed]
        else:
            hooks = []
    except json.JSONDecodeError:
        hooks = None

    # --- Strategy 2: fallback — parse markdown numbered list format ---
    # Handles llama3.1's tendency to return:
    # 1. **"Title here"** (Timestamp: 12.5s – 58.3s)
    # Description text...
    if hooks is None:
        logger.warning("[Ollama] JSON parse failed, attempting markdown fallback parser")
        logger.info(f"[Ollama] Raw response for diagnosis:\n{raw}")
        hooks = _parse_markdown_hooks(raw, total_duration)
        if hooks:
            logger.info(f"[Ollama] Markdown fallback extracted {len(hooks)} hooks")
        else:
            logger.error(f"[Ollama] Raw response (first 500 chars): {raw[:500]}")
            raise RuntimeError(
                f"Ollama ({OLLAMA_MODEL}) returned unrecognisable format for hook detection. "
                "Try a different model (e.g. OLLAMA_MODEL=qwen2.5 in .env)."
            )

    # Validate and clean up timestamps
    validated_hooks = []
    for hook in hooks:
        start = float(hook.get("start_time", 0))
        end = float(hook.get("end_time", 0))
        start = max(0.0, start)
        end = min(end, float(total_duration)) if total_duration > 0 else end

        span = end - start
        logger.info(f"[Ollama] Hook candidate: start={start:.1f}s end={end:.1f}s span={span:.1f}s title='{hook.get('title', '?')[:30]}'")

        # Auto-extend clips that are too short — llama3.1 often copies a single
        # segment's timestamps (1-4s) instead of building a 30-90s window.
        # We rescue these by extending to 45s (capped at video length).
        if span < 30:
            new_end = start + 45.0
            if total_duration > 0:
                new_end = min(new_end, float(total_duration))
            logger.warning(
                f"[Ollama] Auto-extending hook '{hook.get('title','?')[:30]}' "
                f"from {span:.1f}s to {new_end - start:.1f}s (start={start:.1f}s)"
            )
            end = new_end
        elif span > 120:
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
    logger.info(f"[Ollama] Found {len(validated_hooks)} valid hooks")
    return validated_hooks
