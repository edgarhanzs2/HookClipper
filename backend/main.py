"""
AI Hook Clipper — FastAPI Backend
Main application with endpoints for video upload, YouTube URL ingestion,
processing status, clip retrieval, and re-trimming.
"""

import os
import uuid
import logging
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from services.downloader import download_youtube, validate_url
from celery_app import process_video_task

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

# In-memory job index: maps job_id -> {celery_task_id, filename, video_path, ...}
# Actual processing state lives in Redis via Celery.
jobs: dict[str, dict] = {}

# FastAPI app
app = FastAPI(
    title="AI Hook Clipper API",
    description="Upload videos and let AI find the most viral hooks",
    version="2.0.0",
)

# CORS — allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====== Pydantic Models ======

class IngestURLRequest(BaseModel):
    url: str
    mock_ai: str = "false"
    provider: str = "openai"


class RetrimRequest(BaseModel):
    start_time: float
    end_time: float


# ====== Helper: Get Celery task state ======

def _get_task_state(job_id: str) -> dict:
    """Get the current processing state from Celery for a given job."""
    if job_id not in jobs:
        return None

    job_info = jobs[job_id]
    task_id = job_info.get("celery_task_id")
    if not task_id:
        return None

    from celery.result import AsyncResult
    result = AsyncResult(task_id)

    if result.state == "PENDING":
        return {"step": 0, "status": "queued", "job_id": job_id}
    elif result.state == "PROCESSING":
        meta = result.info or {}
        return {
            "step": meta.get("step", 0),
            "status": meta.get("status", "processing"),
            "job_id": job_id,
        }
    elif result.state == "SUCCESS":
        data = result.result or {}
        return {
            "step": 5,
            "status": "completed",
            "job_id": job_id,
            "clips": data.get("clips", []),
            "transcript": data.get("transcript"),
            "video_path": data.get("video_path"),
        }
    elif result.state == "FAILURE":
        meta = result.info or {}
        error_msg = str(meta) if isinstance(meta, Exception) else meta.get("error", "Unknown error")
        return {
            "step": -1,
            "status": "error",
            "job_id": job_id,
            "error": error_msg,
        }
    else:
        return {"step": 0, "status": result.state.lower(), "job_id": job_id}


# ====== API Endpoints ======

@app.get("/")
async def root():
    return {"message": "AI Hook Clipper API", "version": "2.0.0"}


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

    # Dispatch to Celery
    is_mock = mock_ai.lower() == "true"
    task = process_video_task.delay(job_id, video_path, is_mock, provider.lower())

    # Store job index
    jobs[job_id] = {
        "id": job_id,
        "celery_task_id": task.id,
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 1),
        "video_path": video_path,
        "source": "upload",
    }

    return {"job_id": job_id, "status": "processing_started", "filename": file.filename}


@app.post("/api/ingest-url")
async def ingest_url(request: IngestURLRequest):
    """Download a YouTube video by URL and start processing."""

    url = request.url.strip()

    # Validate URL
    if not validate_url(url):
        raise HTTPException(400, "Invalid YouTube URL. Supported: youtube.com/watch, youtu.be, youtube.com/shorts")

    job_id = str(uuid.uuid4())[:8]
    logger.info(f"[{job_id}] Ingesting URL: {url}")

    # Download the video
    try:
        download_result = download_youtube(url, str(UPLOAD_DIR))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(500, f"Download failed: {str(e)}")

    video_path = download_result["video_path"]
    title = download_result["title"]
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

    logger.info(f"[{job_id}] Downloaded: '{title}' ({file_size_mb:.1f}MB)")

    # Dispatch to Celery
    is_mock = request.mock_ai.lower() == "true"
    task = process_video_task.delay(job_id, video_path, is_mock, request.provider.lower())

    # Store job index
    jobs[job_id] = {
        "id": job_id,
        "celery_task_id": task.id,
        "filename": title,
        "file_size_mb": round(file_size_mb, 1),
        "video_path": video_path,
        "source": "youtube",
        "url": url,
    }

    return {"job_id": job_id, "status": "processing_started", "filename": title}


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the current processing status of a job."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    state = _get_task_state(job_id)

    step_labels = {
        0: "Queued",
        1: "Extracting Audio",
        2: "Transcribing",
        3: "Finding Hooks",
        4: "Cutting Clips",
        5: "Complete",
    }

    return {
        "job_id": job_id,
        "status": state["status"],
        "step": state["step"],
        "step_label": step_labels.get(state["step"], "Processing"),
        "filename": jobs[job_id]["filename"],
        "error": state.get("error"),
    }


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get the processed clips for a completed job."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    state = _get_task_state(job_id)

    if state["status"] == "error":
        raise HTTPException(500, f"Job failed: {state.get('error', 'Unknown error')}")

    if state["status"] != "completed":
        raise HTTPException(202, detail="Job still processing")

    # Format clips for the frontend
    formatted_clips = []
    for i, clip in enumerate(state.get("clips", [])):
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
                "start_time_sec": clip["start_time"],
                "end_time_sec": clip["end_time"],
                "score": clip["score"],
                "reason": clip.get("reason", ""),
                "download_url": f"/api/download/{job_id}/{i + 1}",
            })

    return {
        "job_id": job_id,
        "filename": jobs[job_id]["filename"],
        "total_clips": len(formatted_clips),
        "clips": formatted_clips,
    }


@app.post("/api/retrim/{job_id}/{clip_id}")
async def retrim_clip(job_id: str, clip_id: int, request: RetrimRequest):
    """Re-trim a specific clip with new start/end timestamps."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    state = _get_task_state(job_id)

    if state["status"] != "completed":
        raise HTTPException(400, "Job is not completed yet")

    clips = state.get("clips", [])
    clip_index = clip_id - 1

    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(404, f"Clip not found: {clip_id}")

    if request.start_time >= request.end_time:
        raise HTTPException(400, "start_time must be less than end_time")

    if request.end_time - request.start_time < 5:
        raise HTTPException(400, "Clip must be at least 5 seconds long")

    # Get original video path
    video_path = state.get("video_path") or jobs[job_id].get("video_path")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(404, "Original video file not found")

    # Re-trim the clip
    from services.trimmer import trim_clip

    job_output_dir = str(OUTPUT_DIR / job_id)
    os.makedirs(job_output_dir, exist_ok=True)

    output_filename = f"clip_{clip_id}_retrimmed.mp4"
    output_path = os.path.join(job_output_dir, output_filename)

    logger.info(f"[{job_id}] Re-trimming clip {clip_id}: {request.start_time:.1f}s - {request.end_time:.1f}s")

    try:
        trim_clip(video_path, request.start_time, request.end_time, output_path)
    except Exception as e:
        raise HTTPException(500, f"Re-trim failed: {str(e)}")

    return {
        "job_id": job_id,
        "clip_id": clip_id,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "download_url": f"/api/download/{job_id}/{clip_id}",
        "status": "retrimmed",
    }



@app.post("/api/render-vertical/{job_id}/{clip_id}")
async def render_vertical(job_id: str, clip_id: int, style: str = "hormozi"):
    """Render a vertical (9:16) version of a clip with face tracking and subtitles."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    state = _get_task_state(job_id)

    if state["status"] != "completed":
        raise HTTPException(400, "Job is not completed yet")

    clips = state.get("clips", [])
    clip_index = clip_id - 1

    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(404, f"Clip not found: {clip_id}")

    clip = clips[clip_index]
    video_path = state.get("video_path") or jobs[job_id].get("video_path")
    transcript = state.get("transcript", {})

    if not video_path or not os.path.exists(video_path):
        raise HTTPException(404, "Original video file not found")

    valid_styles = ["hormozi", "word_pop", "classic"]
    if style not in valid_styles:
        raise HTTPException(400, f"Invalid style: {style}. Available: {valid_styles}")

    logger.info(f"[{job_id}] Rendering vertical clip {clip_id} with style '{style}'")

    try:
        from services.face_tracker import track_faces
        from services.subtitle_engine import generate_subtitles
        from services.trimmer import trim_and_render_vertical

        # Step 1: Face tracking on the source video
        logger.info(f"[{job_id}] Running face detection...")
        face_data = track_faces(video_path, sample_every_n=10)

        # Step 2: Generate subtitles for this clip's time range
        job_output_dir = str(OUTPUT_DIR / job_id)
        os.makedirs(job_output_dir, exist_ok=True)
        subtitle_path = os.path.join(job_output_dir, f"clip_{clip_id}_subs.ass")

        generate_subtitles(
            transcript=transcript,
            style=style,
            output_path=subtitle_path,
            clip_start=clip["start_time"],
            clip_end=clip["end_time"],
        )

        # Step 3: Render vertical clip
        output_path = os.path.join(job_output_dir, f"clip_{clip_id}_vertical.mp4")

        trim_and_render_vertical(
            video_path=video_path,
            start_time=clip["start_time"],
            end_time=clip["end_time"],
            face_data=face_data,
            subtitle_path=subtitle_path,
            output_path=output_path,
        )

        return {
            "job_id": job_id,
            "clip_id": clip_id,
            "style": style,
            "download_url": f"/api/download-vertical/{job_id}/{clip_id}",
            "status": "rendered",
        }

    except Exception as e:
        logger.error(f"[{job_id}] Vertical render failed: {e}")
        raise HTTPException(500, f"Vertical render failed: {str(e)}")


@app.get("/api/download-vertical/{job_id}/{clip_id}")
async def download_vertical_clip(job_id: str, clip_id: int):
    """Download the vertical (9:16) version of a clip."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    vertical_path = OUTPUT_DIR / job_id / f"clip_{clip_id}_vertical.mp4"
    if not vertical_path.exists():
        raise HTTPException(404, "Vertical clip not found. Render it first via POST /api/render-vertical")

    return FileResponse(
        path=str(vertical_path),
        media_type="video/mp4",
        filename=f"hook_clip_{clip_id}_vertical.mp4",
    )


@app.post("/api/render-landscape-subs/{job_id}/{clip_id}")
async def render_landscape_subs(job_id: str, clip_id: int, style: str = "hormozi"):
    """Render a landscape clip with burned-in subtitles."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    state = _get_task_state(job_id)

    if state["status"] != "completed":
        raise HTTPException(400, "Job is not completed yet")

    clips = state.get("clips", [])
    clip_index = clip_id - 1

    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(404, f"Clip not found: {clip_id}")

    clip = clips[clip_index]
    video_path = state.get("video_path") or jobs[job_id].get("video_path")
    transcript = state.get("transcript", {})

    if not video_path or not os.path.exists(video_path):
        raise HTTPException(404, "Original video file not found")

    valid_styles = ["hormozi", "word_pop", "classic"]
    if style not in valid_styles:
        raise HTTPException(400, f"Invalid style: {style}. Available: {valid_styles}")

    logger.info(f"[{job_id}] Rendering landscape clip {clip_id} with subtitles, style '{style}'")

    try:
        import subprocess
        from services.subtitle_engine import generate_subtitles
        from services.trimmer import trim_and_render_landscape_subs

        # Detect source video dimensions for subtitle sizing
        video_width, video_height = 1920, 1080  # sensible landscape defaults
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=p=0",
                 video_path],
                capture_output=True, text=True, timeout=10,
            )
            if probe.returncode == 0 and probe.stdout.strip():
                parts = probe.stdout.strip().split(",")
                video_width, video_height = int(parts[0]), int(parts[1])
        except Exception:
            logger.warning(f"[{job_id}] Could not detect video dimensions, using defaults")

        # Generate subtitles sized for landscape resolution
        job_output_dir = str(OUTPUT_DIR / job_id)
        os.makedirs(job_output_dir, exist_ok=True)
        subtitle_path = os.path.join(job_output_dir, f"clip_{clip_id}_landscape_subs.ass")

        generate_subtitles(
            transcript=transcript,
            style=style,
            output_path=subtitle_path,
            clip_start=clip["start_time"],
            clip_end=clip["end_time"],
            video_width=video_width,
            video_height=video_height,
        )

        # Render landscape clip with subtitles
        output_path = os.path.join(job_output_dir, f"clip_{clip_id}_landscape_subs.mp4")

        trim_and_render_landscape_subs(
            video_path=video_path,
            start_time=clip["start_time"],
            end_time=clip["end_time"],
            subtitle_path=subtitle_path,
            output_path=output_path,
        )

        return {
            "job_id": job_id,
            "clip_id": clip_id,
            "style": style,
            "download_url": f"/api/download-landscape-subs/{job_id}/{clip_id}",
            "status": "rendered",
        }

    except Exception as e:
        logger.error(f"[{job_id}] Landscape subtitle render failed: {e}")
        raise HTTPException(500, f"Landscape subtitle render failed: {str(e)}")


@app.get("/api/download-landscape-subs/{job_id}/{clip_id}")
async def download_landscape_subs_clip(job_id: str, clip_id: int):
    """Download the landscape version of a clip with burned-in subtitles."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    subs_path = OUTPUT_DIR / job_id / f"clip_{clip_id}_landscape_subs.mp4"
    if not subs_path.exists():
        raise HTTPException(404, "Landscape subtitled clip not found. Render it first.")

    return FileResponse(
        path=str(subs_path),
        media_type="video/mp4",
        filename=f"hook_clip_{clip_id}_subtitled.mp4",
    )


@app.get("/api/download/{job_id}/{clip_id}")
async def download_clip(job_id: str, clip_id: int):
    """Download a specific clip."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job not found: {job_id}")

    # Check for retrimmed version first
    job_output_dir = OUTPUT_DIR / job_id
    retrimmed_path = job_output_dir / f"clip_{clip_id}_retrimmed.mp4"
    if retrimmed_path.exists():
        return FileResponse(
            path=str(retrimmed_path),
            media_type="video/mp4",
            filename=f"hook_clip_{clip_id}.mp4",
        )

    # Otherwise serve original clip from Celery result
    state = _get_task_state(job_id)
    clips = state.get("clips", [])

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
