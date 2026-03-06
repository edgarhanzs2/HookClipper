"""
Subtitle engine for AI Hook Clipper.
Generates .ass (Advanced SubStation Alpha) subtitle files from word-level transcripts.
Supports multiple visual styles for short-form video content.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Available subtitle styles
STYLES = ["hormozi", "word_pop", "classic"]


def _format_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def _group_words_into_lines(words: list[dict], max_words_per_line: int = 4) -> list[dict]:
    """
    Group word-level timestamps into subtitle lines.
    Each line contains up to max_words_per_line words.

    Returns:
        List of {text, start, end, words} dicts
    """
    lines = []
    for i in range(0, len(words), max_words_per_line):
        chunk = words[i : i + max_words_per_line]
        if not chunk:
            continue

        line_text = " ".join(w["word"].strip() for w in chunk)
        line_start = chunk[0]["start"]
        line_end = chunk[-1]["end"]

        lines.append({
            "text": line_text,
            "start": line_start,
            "end": line_end,
            "words": chunk,
        })

    return lines


def _ass_header(style: str, video_width: int = 1080, video_height: int = 1920) -> str:
    """Generate the ASS file header with style definitions."""

    # Scale font sizes relative to the 1920-tall baseline (vertical)
    # For landscape videos, fonts need to be smaller since the video height is less
    scale = video_height / 1920.0

    if style == "hormozi":
        # Bold white text, large, center-bottom, with black outline
        font_size = int(72 * scale)
        style_line = (
            f"Style: Default,Arial,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,"
            "1,0,0,0,100,100,0,0,1,4,2,2,10,10,40,1"
        )
        # Active word highlight style — yellow text
        highlight_line = (
            f"Style: Highlight,Arial,{font_size},&H0000FFFF,&H000000FF,&H00000000,&H80000000,"
            "1,0,0,0,100,100,0,0,1,4,2,2,10,10,40,1"
        )
    elif style == "word_pop":
        # Clean white text, slightly smaller for pop effect
        font_size = int(64 * scale)
        style_line = (
            f"Style: Default,Arial,{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,"
            "1,0,0,0,100,100,0,0,1,3,1,2,10,10,50,1"
        )
        highlight_line = ""
    else:  # classic
        # Standard bottom-center white subtitles
        font_size = int(56 * scale)
        style_line = (
            f"Style: Default,Arial,{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,"
            "0,0,0,0,100,100,0,0,1,3,0,2,10,10,30,1"
        )
        highlight_line = ""

    header = f"""[Script Info]
Title: Hook Clipper Subtitles
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}
{highlight_line}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return header


def _generate_hormozi(lines: list[dict]) -> str:
    """
    Hormozi-style subtitles: each line appears with the current word highlighted in yellow.
    Creates multiple events per line — one for each word being active.
    """
    events = []

    for line in lines:
        words = line["words"]

        for word_idx, active_word in enumerate(words):
            # Build the text with override tags: active word is yellow
            parts = []
            for j, w in enumerate(words):
                word_text = w["word"].strip().upper()
                if j == word_idx:
                    # Active word: yellow color
                    parts.append(f"{{\\c&H00FFFF&}}{word_text}{{\\c&HFFFFFF&}}")
                else:
                    parts.append(word_text)

            text = " ".join(parts)

            start = _format_ass_time(active_word["start"])
            # End at next word's start, or at end of line for last word
            if word_idx < len(words) - 1:
                end = _format_ass_time(words[word_idx + 1]["start"])
            else:
                end = _format_ass_time(active_word["end"])

            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return "\n".join(events)


def _generate_word_pop(lines: list[dict]) -> str:
    """
    Word-pop style: each word appears individually with a scale-up animation.
    Words pop in one at a time using ASS transform tags.
    """
    events = []

    for line in lines:
        words = line["words"]

        for w in words:
            word_text = w["word"].strip().upper()
            start = _format_ass_time(w["start"])
            end = _format_ass_time(w["end"])

            # Pop-in effect: scale from 0 to 100 over 100ms
            text = f"{{\\fscx0\\fscy0\\t(0,100,\\fscx100\\fscy100)}}{word_text}"

            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return "\n".join(events)


def _generate_classic(lines: list[dict]) -> str:
    """
    Classic subtitles: standard bottom text, one line at a time.
    """
    events = []

    for line in lines:
        start = _format_ass_time(line["start"])
        end = _format_ass_time(line["end"])
        text = line["text"]
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return "\n".join(events)


def generate_subtitles(
    transcript: dict,
    style: str = "hormozi",
    output_path: str = "subtitles.ass",
    clip_start: float = 0.0,
    clip_end: float = None,
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """
    Generate an .ass subtitle file from a transcript with word-level timestamps.

    Args:
        transcript: Dict with 'words' list (each: {word, start, end}) and optionally 'segments'
        style: Subtitle style — 'hormozi', 'word_pop', or 'classic'
        output_path: Path to save the .ass file
        clip_start: Start time offset (to align subs with a trimmed clip)
        clip_end: End time (to filter words outside the clip range)
        video_width: Video width for subtitle positioning (default 1080 for vertical)
        video_height: Video height for subtitle positioning (default 1920 for vertical)

    Returns:
        Path to the generated .ass file
    """
    if style not in STYLES:
        raise ValueError(f"Unknown style: {style}. Available: {STYLES}")

    words = transcript.get("words", [])

    # If no word-level timestamps, try to generate from segments
    if not words and transcript.get("segments"):
        logger.warning("No word-level timestamps — falling back to segment-level subtitles")
        for seg in transcript["segments"]:
            # Split segment into rough word estimates
            seg_words = seg["text"].strip().split()
            if not seg_words:
                continue
            seg_duration = seg["end"] - seg["start"]
            word_duration = seg_duration / len(seg_words)
            for i, w in enumerate(seg_words):
                words.append({
                    "word": w,
                    "start": seg["start"] + i * word_duration,
                    "end": seg["start"] + (i + 1) * word_duration,
                })

    if not words:
        logger.warning("No words found in transcript — generating empty subtitle file")
        words = []

    # Filter words to clip range and adjust timestamps
    if clip_start > 0 or clip_end is not None:
        filtered = []
        for w in words:
            if w["end"] < clip_start:
                continue
            if clip_end is not None and w["start"] > clip_end:
                continue
            filtered.append({
                "word": w["word"],
                "start": max(0, w["start"] - clip_start),
                "end": max(0, w["end"] - clip_start),
            })
        words = filtered

    # Group words into lines
    lines = _group_words_into_lines(words, max_words_per_line=4)

    logger.info(f"Generating {style} subtitles: {len(words)} words -> {len(lines)} lines")

    # Generate ASS content
    header = _ass_header(style, video_width=video_width, video_height=video_height)

    if style == "hormozi":
        events = _generate_hormozi(lines)
    elif style == "word_pop":
        events = _generate_word_pop(lines)
    else:
        events = _generate_classic(lines)

    ass_content = header + events + "\n"

    # Write to file
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    logger.info(f"Subtitle file saved: {output_path}")
    return output_path
