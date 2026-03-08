'use client';

import { useState, useCallback, useRef } from 'react';
import BlobBackground from './components/BlobBackground';
import DropZone from './components/DropZone';
import ProcessingView from './components/ProcessingView';
import ClipCard, { Clip } from './components/ClipCard';
import YouTubeInput from './components/YouTubeInput';

type AppState = 'upload' | 'processing' | 'results';
type InputMode = 'file' | 'youtube';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [inputMode, setInputMode] = useState<InputMode>('file');
  const [currentStep, setCurrentStep] = useState(0);
  const [fileName, setFileName] = useState('');
  const [clips, setClips] = useState<Clip[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mockAi, setMockAi] = useState(false);
  const [provider, setProvider] = useState<'openai' | 'gemini' | 'ollama'>('openai');
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const pollStatus = useCallback((jobId: string) => {
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/status/${jobId}`);
        const data = await res.json();

        setCurrentStep(data.step);

        if (data.status === 'completed') {
          stopPolling();
          // Fetch results
          const resultsRes = await fetch(`${API_BASE}/api/results/${jobId}`);
          const resultsData = await resultsRes.json();

          const formattedClips: Clip[] = resultsData.clips.map((clip: any) => ({
            id: clip.id,
            title: clip.title,
            transcript: clip.transcript,
            start: clip.start,
            end: clip.end,
            duration: clip.duration,
            score: clip.score,
            downloadUrl: `${API_BASE}${clip.download_url}`,
            startTimeSec: clip.start_time_sec,
            endTimeSec: clip.end_time_sec,
            jobId: jobId,
          }));

          setClips(formattedClips);
          setAppState('results');
        } else if (data.status === 'error') {
          stopPolling();
          setError(data.error || 'Processing failed. Please try again.');
          setAppState('upload');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);
  }, [stopPolling]);

  const handleFileSelected = useCallback(async (file: File) => {
    setFileName(file.name);
    setAppState('processing');
    setCurrentStep(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mock_ai', mockAi ? 'true' : 'false');
      formData.append('provider', provider);

      const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      const data = await res.json();
      setCurrentJobId(data.job_id);
      pollStatus(data.job_id);
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload video. Is the backend running?');
      setAppState('upload');
    }
  }, [pollStatus, mockAi, provider]);

  const handleYouTubeSubmit = useCallback(async (url: string) => {
    setFileName(url);
    setAppState('processing');
    setCurrentStep(0);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/ingest-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          mock_ai: mockAi ? 'true' : 'false',
          provider,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'URL ingestion failed');
      }

      const data = await res.json();
      setFileName(data.filename || url);
      setCurrentJobId(data.job_id);
      pollStatus(data.job_id);
    } catch (err: any) {
      console.error('URL ingestion error:', err);
      setError(err.message || 'Failed to process YouTube URL. Is the backend running?');
      setAppState('upload');
    }
  }, [pollStatus, mockAi, provider]);

  const handleReset = useCallback(() => {
    stopPolling();
    setAppState('upload');
    setCurrentStep(0);
    setFileName('');
    setClips([]);
    setError(null);
    setCurrentJobId(null);
  }, [stopPolling]);

  return (
    <main className="relative min-h-screen flex flex-col">
      <BlobBackground />

      {/* Header */}
      <header className="relative z-10 w-full py-6 px-8">
        <nav className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{
              background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
            }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <polygon points="23 7 16 12 23 17 23 7" strokeLinecap="round" strokeLinejoin="round" />
                <rect x="1" y="5" width="15" height="14" rx="2" ry="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <span className="text-xl font-bold tracking-tight">
              <span className="gradient-text">Hook</span>
              <span className="text-[var(--color-foreground)]">Clipper</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-3 py-1.5 rounded-full font-semibold" style={{
              background: 'rgba(6,182,212,0.15)',
              color: 'var(--color-accent)',
            }}>
              Phase 2 · Formatting
            </span>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 pb-12">
        {/* ====== UPLOAD VIEW ====== */}
        {appState === 'upload' && (
          <div className="w-full max-w-2xl mx-auto">
            {/* Hero Text */}
            <div className="text-center mb-8 animate-fade-in-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-xs font-medium text-[var(--color-foreground)]/60 mb-6">
                <span className="text-base">⚡</span>
                AI-Powered Hook Detection
              </div>
              <h1 className="text-5xl md:text-6xl font-extrabold mb-4 leading-tight tracking-tight">
                <span className="text-[var(--color-foreground)]">Find </span>
                <span className="gradient-text">Viral Hooks</span>
                <br />
                <span className="text-[var(--color-foreground)]">In Seconds</span>
              </h1>
              <p className="text-lg text-[var(--color-foreground)]/50 max-w-md mx-auto leading-relaxed mb-6">
                Upload your video or paste a YouTube link — AI discovers the most engaging moments for TikTok, Shorts, and Reels.
              </p>

              {/* AI Provider + Mock AI Controls */}
              <div className="flex flex-col items-center gap-4 mb-8 animate-fade-in-up" style={{ animationDelay: '0.2s', opacity: 0 }}>
                {/* Provider Dropdown */}
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-[var(--color-foreground)]/70">AI Provider</span>
                  <div className="relative">
                    <select
                      value={provider}
                      onChange={(e) => setProvider(e.target.value as 'openai' | 'gemini' | 'ollama')}
                      className="appearance-none pl-4 pr-10 py-2 rounded-xl text-sm font-semibold cursor-pointer transition-all duration-200 focus:outline-none"
                      style={{
                        background: 'rgba(139,92,246,0.15)',
                        border: '1px solid rgba(139,92,246,0.3)',
                        color: 'var(--color-primary-light)',
                      }}
                    >
                      <option value="openai">🤖 GPT-4o</option>
                      <option value="gemini">✨ Gemini 2.0 Flash</option>
                      <option value="ollama">🦙 Local AI (Ollama)</option>
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-3 flex items-center">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--color-primary-light)' }}>
                        <polyline points="6 9 12 15 18 9" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Mock AI Toggle */}
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-[var(--color-foreground)]/70">Mock AI Mode</span>
                  <button
                    type="button"
                    onClick={() => setMockAi(!mockAi)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300 focus:outline-none ${mockAi ? 'bg-indigo-500' : 'bg-[var(--color-foreground)]/20'}`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 ${mockAi ? 'translate-x-6' : 'translate-x-1'}`}
                    />
                  </button>
                  <span className="text-xs text-[var(--color-foreground)]/50" title="Skip API calls to save credits.">
                    (Save Credits)
                  </span>
                </div>
              </div>
            </div>

            {/* Error Alert */}
            {error && (
              <div className="mb-6 p-4 rounded-xl text-sm text-center animate-fade-in flex items-center justify-center gap-2" style={{
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.2)',
                color: '#f87171',
              }}>
                <span>⚠️</span> {error}
              </div>
            )}

            {/* Input Mode Tabs */}
            <div className="flex items-center justify-center gap-1 mb-6 animate-fade-in-up" style={{ animationDelay: '0.3s', opacity: 0 }}>
              <button
                onClick={() => setInputMode('file')}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${inputMode === 'file' ? 'text-white' : 'text-[var(--color-foreground)]/50 hover:text-[var(--color-foreground)]/80'
                  }`}
                style={{
                  background: inputMode === 'file'
                    ? 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))'
                    : 'rgba(255,255,255,0.05)',
                  boxShadow: inputMode === 'file' ? '0 4px 15px rgba(139,92,246,0.3)' : 'none',
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
                  <polyline points="17 8 12 3 7 8" strokeLinecap="round" strokeLinejoin="round" />
                  <line x1="12" y1="3" x2="12" y2="15" strokeLinecap="round" />
                </svg>
                Upload File
              </button>
              <button
                onClick={() => setInputMode('youtube')}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${inputMode === 'youtube' ? 'text-white' : 'text-[var(--color-foreground)]/50 hover:text-[var(--color-foreground)]/80'
                  }`}
                style={{
                  background: inputMode === 'youtube'
                    ? 'linear-gradient(135deg, #EF4444, #DC2626)'
                    : 'rgba(255,255,255,0.05)',
                  boxShadow: inputMode === 'youtube' ? '0 4px 15px rgba(239,68,68,0.3)' : 'none',
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                </svg>
                YouTube URL
              </button>
            </div>

            {/* Input Area */}
            <div className="animate-fade-in-up" style={{ animationDelay: '0.4s', opacity: 0 }}>
              {inputMode === 'file' ? (
                <DropZone onFileSelected={handleFileSelected} />
              ) : (
                <YouTubeInput onSubmit={handleYouTubeSubmit} />
              )}
            </div>

            {/* Features Row */}
            <div className="mt-12 grid grid-cols-3 gap-4 animate-fade-in-up" style={{ animationDelay: '0.6s', opacity: 0 }}>
              {[
                { icon: '🧠', label: 'AI Hook Detection', desc: 'AI finds the best moments' },
                { icon: '📱', label: 'Vertical Clips', desc: '9:16 with face tracking' },
                { icon: '💬', label: 'Auto Subtitles', desc: 'Animated subtitle styles' },
              ].map((feat, i) => (
                <div key={i} className="glass rounded-xl p-4 text-center transition-all duration-300 hover:scale-105">
                  <span className="text-2xl block mb-2">{feat.icon}</span>
                  <p className="text-xs font-bold text-[var(--color-foreground)] mb-1">{feat.label}</p>
                  <p className="text-[10px] text-[var(--color-foreground)]/40">{feat.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ====== PROCESSING VIEW ====== */}
        {appState === 'processing' && (
          <ProcessingView currentStep={currentStep} fileName={fileName} />
        )}

        {/* ====== RESULTS VIEW ====== */}
        {appState === 'results' && (
          <div className="w-full max-w-5xl mx-auto">
            {/* Header */}
            <div className="text-center mb-10 animate-fade-in-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold mb-4" style={{
                background: 'rgba(16,185,129,0.15)',
                color: 'var(--color-success)',
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Analysis Complete
              </div>
              <h2 className="text-4xl font-extrabold mb-2">
                <span className="text-[var(--color-foreground)]">We Found </span>
                <span className="gradient-text">{clips.length} Viral Hooks</span>
              </h2>
              <p className="text-[var(--color-foreground)]/50 text-sm">
                From <span className="font-semibold text-[var(--color-foreground)]/70">{fileName}</span>
              </p>
              <p className="text-xs text-[var(--color-foreground)]/30 mt-2">
                Use the 📱 9:16 button on any clip to render vertical video with subtitles
              </p>
            </div>

            {/* Clip Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
              {clips.map((clip, index) => (
                <ClipCard key={clip.id} clip={clip} index={index} />
              ))}
            </div>

            {/* Bottom Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-fade-in-up" style={{ animationDelay: '0.8s', opacity: 0 }}>
              <button
                onClick={handleReset}
                className="px-8 py-3 rounded-xl text-sm font-bold transition-all duration-300 hover:scale-105 active:scale-95 flex items-center gap-2"
                style={{
                  background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
                  color: 'white',
                  boxShadow: '0 4px 20px rgba(139,92,246,0.3)',
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="1 4 1 10 7 10" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Process Another Video
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="relative z-10 py-6 text-center">
        <p className="text-xs text-[var(--color-foreground)]/30">
          Hook Clipper · AI-Powered Content Repurposing · Phase 2
        </p>
      </footer>
    </main>
  );
}
