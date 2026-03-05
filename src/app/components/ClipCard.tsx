'use client';

import { useState } from 'react';
import StylePickerModal from './StylePickerModal';
import TimelineEditor from './TimelineEditor';

export interface Clip {
    id: number;
    title: string;
    transcript: string;
    start: string;
    end: string;
    duration: string;
    score: number;
    downloadUrl?: string;
    startTimeSec?: number;
    endTimeSec?: number;
    jobId?: string;
    maxDuration?: number;
}

interface ClipCardProps {
    clip: Clip;
    index: number;
}

export default function ClipCard({ clip, index }: ClipCardProps) {
    const [showStylePicker, setShowStylePicker] = useState(false);
    const [showTimeline, setShowTimeline] = useState(false);

    const getScoreColor = (score: number) => {
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#f59e0b';
        return '#ef4444';
    };

    const getScoreLabel = (score: number) => {
        if (score >= 80) return '🔥 High Potential';
        if (score >= 60) return '⚡ Good';
        return '💡 Decent';
    };

    return (
        <>
            <div
                className="glass-strong rounded-2xl overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_40px_rgba(139,92,246,0.15)] group animate-fade-in-up"
                style={{ animationDelay: `${index * 0.15}s`, opacity: 0 }}
            >
                {/* Video Placeholder / Thumbnail */}
                <div className="relative aspect-video bg-[var(--color-surface)] flex items-center justify-center overflow-hidden">
                    <div
                        className="absolute inset-0 opacity-30"
                        style={{
                            background: `linear-gradient(${120 + index * 40}deg, rgba(139,92,246,0.3), rgba(6,182,212,0.2))`,
                        }}
                    />
                    {/* Play button */}
                    <button
                        className="relative z-10 w-16 h-16 flex items-center justify-center rounded-full transition-all duration-300 group-hover:scale-110"
                        style={{
                            background: 'rgba(139,92,246,0.8)',
                            backdropFilter: 'blur(8px)',
                            boxShadow: '0 0 30px rgba(139,92,246,0.3)',
                        }}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                            <polygon points="6 3 20 12 6 21 6 3" />
                        </svg>
                    </button>
                    {/* Duration badge */}
                    <div
                        className="absolute bottom-3 right-3 px-2.5 py-1 rounded-lg text-xs font-mono font-bold"
                        style={{
                            background: 'rgba(0,0,0,0.7)',
                            backdropFilter: 'blur(4px)',
                        }}
                    >
                        {clip.duration}
                    </div>
                    {/* Score badge */}
                    <div
                        className="absolute top-3 right-3 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5"
                        style={{
                            background: 'rgba(0,0,0,0.7)',
                            backdropFilter: 'blur(4px)',
                            color: getScoreColor(clip.score),
                        }}
                    >
                        <div className="w-2 h-2 rounded-full" style={{ background: getScoreColor(clip.score) }} />
                        {clip.score}/100
                    </div>
                </div>

                {/* Content */}
                <div className="p-5">
                    {/* Title & Score Label */}
                    <div className="flex items-start justify-between gap-3 mb-3">
                        <h3 className="text-base font-bold text-[var(--color-foreground)] leading-tight">
                            {clip.title}
                        </h3>
                        <span
                            className="text-xs font-medium shrink-0 px-2 py-1 rounded-md"
                            style={{
                                background: `${getScoreColor(clip.score)}20`,
                                color: getScoreColor(clip.score),
                            }}
                        >
                            {getScoreLabel(clip.score)}
                        </span>
                    </div>

                    {/* Transcript Preview */}
                    <p className="text-sm text-[var(--color-foreground)]/50 leading-relaxed line-clamp-3 mb-4">
                        &ldquo;{clip.transcript}&rdquo;
                    </p>

                    {/* Timestamps */}
                    <div className="flex items-center gap-3 mb-5 text-xs text-[var(--color-foreground)]/40 font-mono">
                        <span className="px-2 py-1 rounded-md" style={{ background: 'rgba(139,92,246,0.1)' }}>
                            {clip.start}
                        </span>
                        <span>→</span>
                        <span className="px-2 py-1 rounded-md" style={{ background: 'rgba(6,182,212,0.1)' }}>
                            {clip.end}
                        </span>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2 mb-2">
                        {/* Download Button */}
                        <a
                            href={clip.downloadUrl || '#'}
                            download={`hook_clip_${clip.id}.mp4`}
                            className="flex-1 py-3 rounded-xl text-sm font-bold text-white transition-all duration-300 hover:brightness-110 active:scale-[0.98] flex items-center justify-center gap-2 no-underline"
                            style={{
                                background: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))',
                                boxShadow: '0 4px 20px rgba(139,92,246,0.25)',
                            }}
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
                                <polyline points="7 10 12 15 17 10" strokeLinecap="round" strokeLinejoin="round" />
                                <line x1="12" y1="15" x2="12" y2="3" strokeLinecap="round" />
                            </svg>
                            Download
                        </a>

                        {/* Render Vertical Button */}
                        {clip.jobId && (
                            <button
                                onClick={() => setShowStylePicker(true)}
                                className="py-3 px-4 rounded-xl text-sm font-bold text-white transition-all duration-300 hover:brightness-110 active:scale-[0.98] flex items-center gap-2"
                                style={{
                                    background: 'linear-gradient(135deg, #06b6d4, #0891b2)',
                                    boxShadow: '0 4px 20px rgba(6,182,212,0.25)',
                                }}
                                title="Render 9:16 vertical clip with subtitles"
                            >
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <rect x="6" y="2" width="12" height="20" rx="2" />
                                    <polygon points="10 8 16 12 10 16 10 8" fill="currentColor" stroke="none" />
                                </svg>
                                9:16
                            </button>
                        )}
                    </div>

                    {/* Timeline Editor Toggle */}
                    {clip.jobId && clip.startTimeSec !== undefined && clip.endTimeSec !== undefined && (
                        <>
                            <button
                                onClick={() => setShowTimeline(!showTimeline)}
                                className="w-full py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center justify-center gap-1.5"
                                style={{
                                    background: showTimeline ? 'rgba(139,92,246,0.15)' : 'rgba(255,255,255,0.05)',
                                    color: showTimeline ? 'var(--color-primary-light)' : 'var(--color-foreground)',
                                    opacity: showTimeline ? 1 : 0.5,
                                }}
                            >
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="6" cy="6" r="3" />
                                    <circle cx="6" cy="18" r="3" />
                                    <line x1="20" y1="4" x2="8.12" y2="15.88" />
                                    <line x1="14.47" y1="14.48" x2="20" y2="20" />
                                    <line x1="8.12" y1="8.12" x2="12" y2="12" />
                                </svg>
                                {showTimeline ? 'Hide Timeline' : 'Adjust Timeline'}
                            </button>

                            {showTimeline && (
                                <TimelineEditor
                                    jobId={clip.jobId}
                                    clipId={clip.id}
                                    startTime={clip.startTimeSec}
                                    endTime={clip.endTimeSec}
                                    maxDuration={clip.maxDuration || clip.endTimeSec + 30}
                                />
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Style Picker Modal */}
            {clip.jobId && (
                <StylePickerModal
                    isOpen={showStylePicker}
                    onClose={() => setShowStylePicker(false)}
                    jobId={clip.jobId}
                    clipId={clip.id}
                />
            )}
        </>
    );
}
