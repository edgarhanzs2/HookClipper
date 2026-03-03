'use client';

export interface Clip {
    id: number;
    title: string;
    transcript: string;
    start: string;
    end: string;
    duration: string;
    score: number;
    downloadUrl?: string;
}

interface ClipCardProps {
    clip: Clip;
    index: number;
}

export default function ClipCard({ clip, index }: ClipCardProps) {
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
        <div
            className="glass-strong rounded-2xl overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_40px_rgba(139,92,246,0.15)] group animate-fade-in-up"
            style={{ animationDelay: `${index * 0.15}s`, opacity: 0 }}
        >
            {/* Video Placeholder / Thumbnail */}
            <div className="relative aspect-video bg-[var(--color-surface)] flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0 opacity-30" style={{
                    background: `linear-gradient(${120 + index * 40}deg, rgba(139,92,246,0.3), rgba(6,182,212,0.2))`,
                }} />
                {/* Play button */}
                <button className="relative z-10 w-16 h-16 flex items-center justify-center rounded-full transition-all duration-300 group-hover:scale-110" style={{
                    background: 'rgba(139,92,246,0.8)',
                    backdropFilter: 'blur(8px)',
                    boxShadow: '0 0 30px rgba(139,92,246,0.3)',
                }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                        <polygon points="6 3 20 12 6 21 6 3" />
                    </svg>
                </button>
                {/* Duration badge */}
                <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-lg text-xs font-mono font-bold" style={{
                    background: 'rgba(0,0,0,0.7)',
                    backdropFilter: 'blur(4px)',
                }}>
                    {clip.duration}
                </div>
                {/* Score badge */}
                <div className="absolute top-3 right-3 px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5" style={{
                    background: 'rgba(0,0,0,0.7)',
                    backdropFilter: 'blur(4px)',
                    color: getScoreColor(clip.score),
                }}>
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
                    <span className="text-xs font-medium shrink-0 px-2 py-1 rounded-md" style={{
                        background: `${getScoreColor(clip.score)}20`,
                        color: getScoreColor(clip.score),
                    }}>
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

                {/* Download Button */}
                <a
                    href={clip.downloadUrl || '#'}
                    download={`hook_clip_${clip.id}.mp4`}
                    className="w-full py-3 rounded-xl text-sm font-bold text-white transition-all duration-300 hover:brightness-110 active:scale-[0.98] flex items-center justify-center gap-2 no-underline"
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
                    Download Clip
                </a>
            </div>
        </div>
    );
}
