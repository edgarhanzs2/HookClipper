'use client';

import { useState, useCallback, useRef } from 'react';
import BlobBackground from './components/BlobBackground';
import DropZone from './components/DropZone';
import ProcessingView from './components/ProcessingView';
import ClipCard, { Clip } from './components/ClipCard';

type AppState = 'upload' | 'processing' | 'results';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [currentStep, setCurrentStep] = useState(0);
  const [fileName, setFileName] = useState('');
  const [clips, setClips] = useState<Clip[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mockAi, setMockAi] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

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

      const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      const data = await res.json();
      // Start polling for status
      pollStatus(data.job_id);
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload video. Is the backend running?');
      setAppState('upload');
    }
  }, [pollStatus]);

  const handleReset = useCallback(() => {
    stopPolling();
    setAppState('upload');
    setCurrentStep(0);
    setFileName('');
    setClips([]);
    setError(null);
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
              background: 'rgba(139,92,246,0.15)',
              color: 'var(--color-primary-light)',
            }}>
              Phase 1 · MVP
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
            <div className="text-center mb-12 animate-fade-in-up">
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
                Upload your video and let AI discover the most engaging moments for TikTok, Shorts, and Reels.
              </p>

              {/* Mock AI Toggle */}
              <div className="flex items-center justify-center gap-3 mb-8 animate-fade-in-up" style={{ animationDelay: '0.2s', opacity: 0 }}>
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
                <span className="text-xs text-[var(--color-foreground)]/50" title="Skip OpenAI calls to save credits. Uses dummy text but still cuts video with FFmpeg.">
                  (Save Credits)
                </span>
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

            {/* Drop Zone */}
            <DropZone onFileSelected={handleFileSelected} />

            {/* Features Row */}
            <div className="mt-12 grid grid-cols-3 gap-4 animate-fade-in-up" style={{ animationDelay: '0.6s', opacity: 0 }}>
              {[
                { icon: '🧠', label: 'AI Hook Detection', desc: 'GPT-4o finds the best moments' },
                { icon: '⚡', label: 'Lightning Fast', desc: 'Results in under 2 minutes' },
                { icon: '📥', label: 'Instant Download', desc: 'Ready-to-post MP4 clips' },
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
          Hook Clipper · AI-Powered Content Repurposing · Phase 1 MVP
        </p>
      </footer>
    </main>
  );
}
