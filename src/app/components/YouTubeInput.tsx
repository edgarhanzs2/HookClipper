'use client';

import { useState } from 'react';

interface YouTubeInputProps {
    onSubmit: (url: string) => void;
    disabled?: boolean;
}

export default function YouTubeInput({ onSubmit, disabled }: YouTubeInputProps) {
    const [url, setUrl] = useState('');
    const [error, setError] = useState<string | null>(null);

    const validateUrl = (input: string): boolean => {
        const patterns = [
            /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]+/,
            /^(https?:\/\/)?(www\.)?youtu\.be\/[\w-]+/,
            /^(https?:\/\/)?(www\.)?youtube\.com\/shorts\/[\w-]+/,
        ];
        return patterns.some((p) => p.test(input.trim()));
    };

    const handleSubmit = () => {
        setError(null);
        const trimmed = url.trim();

        if (!trimmed) {
            setError('Please enter a YouTube URL');
            return;
        }

        if (!validateUrl(trimmed)) {
            setError('Invalid YouTube URL. Supported: youtube.com/watch, youtu.be, youtube.com/shorts');
            return;
        }

        onSubmit(trimmed);
    };

    return (
        <div className="w-full animate-fade-in-up">
            <div
                className="glass-strong rounded-2xl p-8 transition-all duration-300"
                style={{
                    border: '1px solid rgba(139,92,246,0.2)',
                }}
            >
                {/* YouTube icon + label */}
                <div className="flex items-center gap-3 mb-5">
                    <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{ background: 'rgba(239,68,68,0.15)' }}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="#EF4444">
                            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-[var(--color-foreground)]">
                            YouTube URL
                        </h3>
                        <p className="text-xs text-[var(--color-foreground)]/40">
                            Paste a link and we&apos;ll download & analyze it
                        </p>
                    </div>
                </div>

                {/* Input + Button */}
                <div className="flex gap-3">
                    <div className="flex-1 relative">
                        <input
                            type="url"
                            value={url}
                            onChange={(e) => {
                                setUrl(e.target.value);
                                setError(null);
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !disabled) handleSubmit();
                            }}
                            placeholder="https://youtube.com/watch?v=..."
                            disabled={disabled}
                            className="w-full px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/50"
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                border: error
                                    ? '1px solid rgba(239,68,68,0.5)'
                                    : '1px solid rgba(139,92,246,0.2)',
                                color: 'var(--color-foreground)',
                            }}
                        />
                    </div>
                    <button
                        onClick={handleSubmit}
                        disabled={disabled || !url.trim()}
                        className="px-6 py-3.5 rounded-xl text-sm font-bold text-white transition-all duration-300 hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 shrink-0"
                        style={{
                            background:
                                'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
                            boxShadow: '0 4px 20px rgba(139,92,246,0.3)',
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
                            <circle cx="11" cy="11" r="8" />
                            <line x1="21" y1="21" x2="16.65" y2="16.65" />
                        </svg>
                        Analyze
                    </button>
                </div>

                {/* Error message */}
                {error && (
                    <p
                        className="mt-3 text-xs font-medium animate-fade-in"
                        style={{ color: '#f87171' }}
                    >
                        ⚠️ {error}
                    </p>
                )}
            </div>
        </div>
    );
}
