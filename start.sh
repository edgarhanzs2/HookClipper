#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  AI Hook Clipper — Start All Services
#  Opens 4 Terminal tabs: Redis, Backend API, Celery Worker, Frontend
# ═══════════════════════════════════════════════════════════════

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "🎬 Starting AI Hook Clipper..."
echo "   Project: $PROJECT_DIR"
echo ""

# ── Use AppleScript to open new Terminal tabs ──
osascript <<EOF

tell application "Terminal"
    activate

    -- Tab 1: Redis
    do script "echo '🔴 Starting Redis...' && redis-server"
    delay 0.5

    -- Tab 2: Backend API (FastAPI + Uvicorn)
    tell application "System Events" to keystroke "t" using command down
    delay 0.3
    do script "cd '$BACKEND_DIR' && source venv/bin/activate && echo '⚡ Starting Backend API on :8000...' && uvicorn main:app --reload --port 8000" in front window

    -- Tab 3: Celery Worker
    tell application "System Events" to keystroke "t" using command down
    delay 0.3
    do script "cd '$BACKEND_DIR' && source venv/bin/activate && echo '🔄 Starting Celery Worker...' && celery -A celery_app.celery worker --loglevel=info --pool=solo" in front window

    -- Tab 4: Frontend (Next.js)
    tell application "System Events" to keystroke "t" using command down
    delay 0.3
    do script "cd '$PROJECT_DIR' && echo '🖥️  Starting Frontend on :3000...' && npm run dev" in front window

end tell

EOF

echo "✅ All services launching in Terminal tabs!"
echo ""
echo "   🔴 Redis        → localhost:6379"
echo "   ⚡ Backend API   → http://localhost:8000"
echo "   🔄 Celery Worker → Processing queue"
echo "   🖥️  Frontend     → http://localhost:3000"
echo ""
echo "   Open http://localhost:3000 in your browser to start!"
