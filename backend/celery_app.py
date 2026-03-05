"""
Celery application for AI Hook Clipper.
Handles async video processing tasks using Redis as broker/backend.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Ensure the backend directory is on the Python path
# (Celery worker forks may not inherit the correct cwd)
_BASE = str(Path(__file__).parent)
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Redis URL from env or default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery app
celery = Celery(
    "hook_clipper",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    result_expires=3600,  # Results expire after 1 hour
)

# Directories (same as main.py)
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"


@celery.task(bind=True, name="process_video")
def process_video_task(self, job_id: str, video_path: str, mock_ai: bool = False, provider: str = "openai"):
    """
    Full video processing pipeline as a Celery task.
    Updates task state at each step so the API can poll progress.
    """
    # Ensure the backend directory is on sys.path for forked worker processes
    import sys
    from pathlib import Path
    _base = str(Path(__file__).parent)
    if _base not in sys.path:
        sys.path.insert(0, _base)

    from services.audio import extract_audio
    from services.transcription import transcribe_audio as transcribe_openai
    from services.transcription_gemini import transcribe_audio as transcribe_gemini
    from services.transcription_ollama import transcribe_audio as transcribe_ollama
    from services.hooks import detect_hooks as detect_hooks_openai
    from services.hooks_gemini import detect_hooks as detect_hooks_gemini
    from services.hooks_ollama import detect_hooks as detect_hooks_ollama
    from services.trimmer import trim_all_clips

    def update_state(step: int, status: str, **extra):
        self.update_state(
            state="PROCESSING",
            meta={"step": step, "status": status, "job_id": job_id, **extra},
        )

    try:
        # Step 1: Extract audio
        update_state(1, "extracting_audio")
        logger.info(f"[{job_id}] Step 1: Extracting audio...")
        audio_path = extract_audio(video_path, str(UPLOAD_DIR))

        # Step 2: Transcribe
        update_state(2, "transcribing")
        logger.info(f"[{job_id}] Step 2: Transcribing (Mock: {mock_ai}, Provider: {provider})...")
        if mock_ai:
            time.sleep(2)
            transcript = {"text": "This is a mock transcript.", "segments": [], "duration": 10.0}
        elif provider == "gemini":
            transcript = transcribe_gemini(audio_path)
        elif provider == "ollama":
            transcript = transcribe_ollama(audio_path)
        else:
            transcript = transcribe_openai(audio_path)

        # Step 3: Detect hooks
        update_state(3, "detecting_hooks")
        logger.info(f"[{job_id}] Step 3: Detecting hooks (Mock: {mock_ai}, Provider: {provider})...")
        if mock_ai:
            time.sleep(2)
            hooks = [
                {
                    "title": "Mock Hook 1",
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "duration": 60.0,
                    "transcript_snippet": "This is a mocked 60-second hook to save API credits.",
                    "reason": "Mock AI mode is enabled.",
                    "score": 98,
                }
            ]
        elif provider == "gemini":
            hooks = detect_hooks_gemini(transcript)
        elif provider == "ollama":
            hooks = detect_hooks_ollama(transcript)
        else:
            hooks = detect_hooks_openai(transcript)

        # Step 4: Trim clips
        update_state(4, "trimming_clips")
        logger.info(f"[{job_id}] Step 4: Trimming {len(hooks)} clips...")
        job_output_dir = str(OUTPUT_DIR / job_id)
        clips = trim_all_clips(video_path, hooks, job_output_dir, job_id)

        # Cleanup audio file
        try:
            os.remove(audio_path)
        except Exception:
            pass

        logger.info(f"[{job_id}] ✅ Processing complete! {len(clips)} clips generated.")

        return {
            "step": 5,
            "status": "completed",
            "job_id": job_id,
            "clips": clips,
            "transcript": transcript,
            "video_path": video_path,
        }

    except Exception as e:
        logger.error(f"[{job_id}] ❌ Processing failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"step": -1, "status": "error", "job_id": job_id, "error": str(e)},
        )
        raise
