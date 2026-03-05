'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface StylePickerModalProps {
    isOpen: boolean;
    onClose: () => void;
    jobId: string;
    clipId: number;
}

const STYLES = [
    {
        id: 'hormozi',
        name: 'Hormozi Bold',
        emoji: '💪',
        description: 'Bold white text with active word highlighted in yellow. Alex Hormozi inspired.',
        preview: 'THIS IS **HIGHLIGHTED** TEXT',
        colors: ['#FFFFFF', '#FFFF00'],
    },
    {
        id: 'word_pop',
        name: 'Word Pop',
        emoji: '✨',
        description: 'Each word pops in with a scale-up animation. Eye-catching and dynamic.',
        preview: 'WORDS POP IN ONE BY ONE',
        colors: ['#FFFFFF', '#8B5CF6'],
    },
    {
        id: 'classic',
        name: 'Classic',
        emoji: '📝',
        description: 'Standard bottom-center white subtitles. Clean and professional.',
        preview: 'Clean subtitle text at the bottom',
        colors: ['#FFFFFF', '#94A3B8'],
    },
];

export default function StylePickerModal({
    isOpen,
    onClose,
    jobId,
    clipId,
}: StylePickerModalProps) {
    const [selectedStyle, setSelectedStyle] = useState<string | null>(null);
    const [rendering, setRendering] = useState(false);
    const [result, setResult] = useState<{ downloadUrl: string; style: string } | null>(null);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleRender = async (styleId: string) => {
        setSelectedStyle(styleId);
        setRendering(true);
        setError(null);
        setResult(null);

        try {
            const res = await fetch(
                `${API_BASE}/api/render-vertical/${jobId}/${clipId}?style=${styleId}`,
                { method: 'POST' }
            );

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Render failed');
            }

            const data = await res.json();
            setResult({
                downloadUrl: `${API_BASE}${data.download_url}`,
                style: styleId,
            });
        } catch (err: any) {
            setError(err.message || 'Failed to render vertical clip');
        } finally {
            setRendering(false);
        }
    };

    const handleClose = () => {
        setSelectedStyle(null);
        setRendering(false);
        setResult(null);
        setError(null);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={handleClose}
            />

            {/* Modal */}
            <div
                className="relative w-full max-w-lg glass-strong rounded-2xl p-6 animate-fade-in-up"
                style={{
                    border: '1px solid rgba(139,92,246,0.2)',
                    boxShadow: '0 24px 80px rgba(0,0,0,0.5)',
                }}
            >
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-lg font-bold text-[var(--color-foreground)]">
                            🎬 Render Vertical Clip
                        </h2>
                        <p className="text-xs text-[var(--color-foreground)]/40 mt-1">
                            Choose a subtitle style for your 9:16 clip
                        </p>
                    </div>
                    <button
                        onClick={handleClose}
                        className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 hover:bg-white/10"
                    >
                        <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                        >
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                </div>

                {/* Style Cards */}
                <div className="space-y-3 mb-6">
                    {STYLES.map((style) => (
                        <button
                            key={style.id}
                            onClick={() => handleRender(style.id)}
                            disabled={rendering}
                            className={`w-full text-left p-4 rounded-xl transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed ${selectedStyle === style.id
                                    ? 'ring-2 ring-[var(--color-primary)]'
                                    : ''
                                }`}
                            style={{
                                background:
                                    selectedStyle === style.id
                                        ? 'rgba(139,92,246,0.15)'
                                        : 'rgba(255,255,255,0.05)',
                                border: '1px solid rgba(139,92,246,0.15)',
                            }}
                        >
                            <div className="flex items-start gap-3">
                                <span className="text-2xl">{style.emoji}</span>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-sm font-bold text-[var(--color-foreground)]">
                                            {style.name}
                                        </h3>
                                        {rendering && selectedStyle === style.id && (
                                            <div className="w-4 h-4 rounded-full border-2 border-[var(--color-primary)] border-t-transparent animate-spin" />
                                        )}
                                        {result && result.style === style.id && (
                                            <svg
                                                width="16"
                                                height="16"
                                                viewBox="0 0 24 24"
                                                fill="none"
                                                stroke="#10b981"
                                                strokeWidth="3"
                                            >
                                                <polyline points="20 6 9 17 4 12" />
                                            </svg>
                                        )}
                                    </div>
                                    <p className="text-xs text-[var(--color-foreground)]/40 mt-0.5">
                                        {style.description}
                                    </p>
                                    {/* Mini preview */}
                                    <div
                                        className="mt-2 px-3 py-1.5 rounded-md text-xs font-bold tracking-wide"
                                        style={{
                                            background: 'rgba(0,0,0,0.4)',
                                            color: style.colors[0],
                                        }}
                                    >
                                        {style.preview}
                                    </div>
                                </div>
                            </div>
                        </button>
                    ))}
                </div>

                {/* Error */}
                {error && (
                    <div
                        className="p-3 rounded-xl text-xs text-center mb-4 animate-fade-in"
                        style={{
                            background: 'rgba(239,68,68,0.1)',
                            border: '1px solid rgba(239,68,68,0.2)',
                            color: '#f87171',
                        }}
                    >
                        ⚠️ {error}
                    </div>
                )}

                {/* Download result */}
                {result && (
                    <a
                        href={result.downloadUrl}
                        download={`hook_clip_${clipId}_vertical.mp4`}
                        className="w-full py-3 rounded-xl text-sm font-bold text-white transition-all duration-300 hover:brightness-110 active:scale-[0.98] flex items-center justify-center gap-2 no-underline animate-fade-in"
                        style={{
                            background: 'linear-gradient(135deg, #10b981, #059669)',
                            boxShadow: '0 4px 20px rgba(16,185,129,0.3)',
                        }}
                    >
                        <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                        >
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="7 10 12 15 17 10" />
                            <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Download Vertical Clip (9:16)
                    </a>
                )}
            </div>
        </div>
    );
}
