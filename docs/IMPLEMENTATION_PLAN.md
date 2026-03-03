# Phase 1 MVP — AI Hook Clipper

Build a stunning, modern web application that allows users to upload a video, have AI find the best hooks, and download trimmed clips. The UI should be visually premium with engaging animations so users never feel bored while waiting.

## Proposed Changes

### Frontend (Next.js App)

Since this is a brand-new project, we'll scaffold with Next.js (App Router) and build 3 core views in a single-page flow.

#### [NEW] Project setup via `create-next-app`
- Next.js 14+ with App Router, TypeScript, Tailwind CSS
- Google Fonts (Inter / Outfit) for premium typography

---

#### [NEW] `app/page.tsx` — Main Page (Single-page app with state-driven views)
The entire Phase 1 UX lives in one page with 3 states:

**State 1: Upload View**
- Dark-themed hero section with gradient background
- Animated drag-and-drop zone with glowing border animation
- File type validation (`.mp4`, `.mov`), size display
- Animated upload button with ripple effect

**State 2: Processing View (the "don't be bored" experience)**
- Multi-step progress indicator with animated transitions
- Steps: Uploading → Extracting Audio → Transcribing → Analyzing Hooks → Cutting Clips
- Animated waveform/audio visualization while processing
- Fun "Did You Know?" rotating tips about content creation
- Pulsing/morphing blob background animation
- Estimated time remaining

**State 3: Results View**
- Card grid of generated clips
- Each card: embedded video player, hook title, transcript snippet, download button
- Glassmorphism card design with hover effects
- "Process Another" button to reset

---

#### [NEW] `app/globals.css` — Design System
- CSS custom properties for colors, gradients, spacing
- Keyframe animations: pulse, glow, shimmer, float, wave
- Glassmorphism utility classes
- Dark theme as default

---

#### [NEW] `app/components/` — Reusable Components
- `DropZone.tsx` — Animated drag-and-drop file upload
- `ProcessingView.tsx` — Multi-step progress with animations
- `WaveformAnimation.tsx` — Animated audio waveform SVG
- `ClipCard.tsx` — Result card for each generated clip
- `ProgressSteps.tsx` — Step indicator with animated transitions
- `FunFacts.tsx` — Rotating "Did You Know?" cards
- `BlobBackground.tsx` — Animated morphing gradient blob

---

### Backend (Python FastAPI)

#### [NEW] `backend/main.py` — FastAPI application
- `POST /api/upload` — Accepts multipart file upload, kicks off processing, returns job ID
- `GET /api/status/{job_id}` — Returns current processing step and progress
- `GET /api/results/{job_id}` — Returns list of clips with metadata
- `GET /api/download/{job_id}/{clip_id}` — Serves the trimmed clip file
- CORS middleware for Next.js frontend

#### [NEW] `backend/services/audio.py` — Audio Extraction
- Uses `ffmpeg` subprocess to extract audio from uploaded video

#### [NEW] `backend/services/transcription.py` — Transcription
- Integrates with Deepgram or OpenAI Whisper API
- Returns word-level timestamps

#### [NEW] `backend/services/hooks.py` — Hook Detection
- Sends transcript to OpenAI GPT-4o
- Parses structured JSON response for hooks with timestamps
- Validates timestamps against transcript data

#### [NEW] `backend/services/trimmer.py` — Video Trimming
- Uses `ffmpeg` to cut clips at specified timestamps

#### [NEW] `backend/requirements.txt` — Dependencies
- `fastapi`, `uvicorn`, `python-multipart`, `openai`, `httpx`, `python-dotenv`

---

## User Review Required

> [!IMPORTANT]
> **API Keys Needed:** The backend requires API keys for:
> - **OpenAI API** (for GPT-4o hook detection)
> - **Deepgram API** (for transcription) — OR we can use OpenAI Whisper instead (free/local but slower)
>
> For now, I'll build the backend with mock/simulated responses so the full UI flow can be tested without API keys. The mock will return realistic fake data after a short delay. You can plug in real keys later via `.env`.

> [!NOTE]
> **FFmpeg Required:** The backend depends on `ffmpeg` being installed on the system. macOS: `brew install ffmpeg`.

## Verification Plan

### Browser Testing
- Open the app at `http://localhost:3000`
- Test file upload via drag-and-drop and click
- Verify all loading animations play smoothly
- Verify results page renders with clip cards
- Test download button

### Backend Testing
- Test `POST /api/upload` with a sample video file
- Test `GET /api/status/{job_id}` returns progressive status updates
- Test `GET /api/results/{job_id}` returns clip metadata
