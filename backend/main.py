"""
AI Hook Clipper — FastAPI Backend
Main application with endpoints for video upload, processing, and clip retrieval.
"""

import os
import uuid
import asyncio
import logging
from typing import Optional
from pathlib import Path
from threading import Thread
import time

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from services.audio import extract_audio
from services.transcription import transcribe_audio as transcribe_openai
from services.transcription_gemini import transcribe_audio as transcribe_gemini
from services.transcription_ollama import transcribe_audio as transcribe_ollama
from services.hooks import detect_hooks as detect_hooks_openai
from services.hooks_gemini import detect_hooks as detect_hooks_gemini
from services.hooks_ollama import detect_hooks as detect_hooks_ollama
from services.trimmer import trim_all_clips

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory job store (for MVP — in production, use Redis or a database)
jobs: dict[str, dict] = {}

# FastAPI app
app = FastAPI(
    title="AI Hook Clipper API",
    description="Upload videos and let AI find the most viral hooks",
    version="1.0.0",
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====== Processing Pipeline (runs in background thread) ======

def process_video(job_id: str, video_path: str):
    """
    Full processing pipeline:
    1. Extract audio (FFmpeg)
    2. Transcribe (OpenAI Whisper)
    3. Detect hooks (GPT-4o)
    4. Trim clips (FFmpeg)
    """
    try:
        job = jobs[job_id]
        is_mock = job.get("mock_ai", False)

        # Step 1: Extract audio
        job["step"] = 1
        job["status"] = "extracting_audio"
        logger.info(f"[{job_id}] Step 1: Extracting audio...")
        audio_path = extract_audio(video_path, str(UPLOAD_DIR))

        # Step 2: Transcribe
        job["step"] = 2
        job["status"] = "transcribing"
        provider = job.get("provider", "openai")
        logger.info(f"[{job_id}] Step 2: Transcribing (Mock: {is_mock}, Provider: {provider})...")
        if is_mock:
            time.sleep(2)
            transcript = {"text": "This is a mock transcript.", "segments": [], "duration": 10.0}
        elif provider == "gemini":
            transcript = transcribe_gemini(audio_path)
        elif provider == "ollama":
            transcript = transcribe_ollama(audio_path)
        else:
            transcript = transcribe_openai(audio_path)
            
        job["transcript"] = transcript

        # Step 3: Detect hooks
        job["step"] = 3
        job["status"] = "detecting_hooks"
        logger.info(f"[{job_id}] Step 3: Detecting hooks (Mock: {is_mock}, Provider: {provider})...")
        if is_mock:
            time.sleep(2)
            hooks = [
                {
                    "title": "Mock Hook 1",
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "duration": 60.0,
                    "transcript_snippet": "This is a mocked 60-second hook to save API credits.",
                    "reason": "Mock AI mode is enabled.",
                    "score": 98
                }
            ]
        elif provider == "gemini":
            hooks = detect_hooks_gemini(transcript)
        elif provider == "ollama":
            hooks = detect_hooks_ollama(transcript)
        else:
            hooks = detect_hooks_openai(transcript)

        # Step 4: Trim clips
        job["step"] = 4
        job["status"] = "trimming_clips"
        logger.info(f"[{job_id}] Step 4: Trimming {len(hooks)} clips...")
        job_output_dir = str(OUTPUT_DIR / job_id)
        clips = trim_all_clips(video_path, hooks, job_output_dir, job_id)

        # Done
        job["step"] = 5
        job["status"] = "completed"
        job["clips"] = clips
        logger.info(f"[{job_id}] ✅ Processing complete! {len(clips)} clips generated.")

        # Cleanup audio file
        try:
            os.remove(audio_path)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"[{job_id}] ❌ Processing failed: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


# ====== API Endpoints ======

@app.get("/")
async def root():
    return {"message": "AI Hook Clipper API", "version": "1.0.0"}


@app.post("/api/upload")
async def upload_video(
    file: UploadFile = File(...),
    mock_ai: str = Form("false"),
    provider: str = Form("openai"),
):
    """Upload a video file and start processing."""
    
    # Validate file type
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Invalid file type: {file.content_type}. Allowed: {allowed_types}")

    # Generate job ID
    job_id = str(uuid.uuid4())[:8]

    # Save uploaded file
    safe_filename = f"{job_id}_{file.filename.replace(' ', '_')}"
    video_path = str(UPLOAD_DIR / safe_filename)

    logger.info(f"[{job_id}] Uploading: {file.filename} ({file.content_type})")

    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    logger.info(f"[{job_id}] Saved: {video_path} ({file_size_mb:.1f}MB)")

    # Create job record
    jobs[job_id] = {
        "id": job_id,
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 1),
        "video_path": video_path,
        "status": "uploading",
        "step": 0,
        "clips": [],
        "transcript": None,
        "error": None,
        "mock_ai": mock_ai.lower() == "true",
        "provider": provider.lower(),
    }

    # Start processing in background thread
    thread = Thread(target=process_video, args=(job_id, video_path), daemon=True)
    thread.start()

    return {"job_id": job_id, "status": "processing_started", "filename": file.filename}


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the current processing status of a job."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    job = jobs[job_id]

    step_labels = {
        0: "Uploading",
        1: "Extracting Audio",
        2: "Transcribing",
        3: "Finding Hooks",
        4: "Cutting Clips",
        5: "Complete",
    }

    return {
        "job_id": job_id,
        "status": job["status"],
        "step": job["step"],
        "step_label": step_labels.get(job["step"], "Unknown"),
        "filename": job["filename"],
        "error": job["error"],
    }


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get the processed clips for a completed job."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    job = jobs[job_id]

    if job["status"] == "error":
        raise HTTPException(500, f"Job failed: {job['error']}")

    if job["status"] != "completed":
        raise HTTPException(202, detail="Job still processing")

    # Format clips for the frontend
    formatted_clips = []
    for i, clip in enumerate(job.get("clips", [])):
        if clip.get("clip_path") and os.path.exists(clip["clip_path"]):
            # Convert seconds to MM:SS format
            start_min = int(clip["start_time"] // 60)
            start_sec = int(clip["start_time"] % 60)
            end_min = int(clip["end_time"] // 60)
            end_sec = int(clip["end_time"] % 60)
            dur_sec = int(clip["duration"])

            formatted_clips.append({
                "id": i + 1,
                "title": clip["title"],
                "transcript": clip.get("transcript_snippet", ""),
                "start": f"{start_min:02d}:{start_sec:02d}",
                "end": f"{end_min:02d}:{end_sec:02d}",
                "duration": f"{dur_sec // 60}:{dur_sec % 60:02d}",
                "score": clip["score"],
                "reason": clip.get("reason", ""),
                "download_url": f"/api/download/{job_id}/{i + 1}",
            })

    return {
        "job_id": job_id,
        "filename": job["filename"],
        "total_clips": len(formatted_clips),
        "clips": formatted_clips,
    }


@app.get("/api/download/{job_id}/{clip_id}")
async def download_clip(job_id: str, clip_id: int):
    """Download a specific clip."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    job = jobs[job_id]
    clips = job.get("clips", [])

    clip_index = clip_id - 1
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(404, f"Clip not found: {clip_id}")

    clip = clips[clip_index]
    clip_path = clip.get("clip_path")

    if not clip_path or not os.path.exists(clip_path):
        raise HTTPException(404, "Clip file not found on disk")

    return FileResponse(
        path=clip_path,
        media_type="video/mp4",
        filename=f"hook_clip_{clip_id}.mp4",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
