'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface TimelineEditorProps {
    jobId: string;
    clipId: number;
    startTime: number;
    endTime: number;
    maxDuration: number;
    onRetrimmed?: (newDownloadUrl: string) => void;
}

export default function TimelineEditor({
    jobId,
    clipId,
    startTime,
    endTime,
    maxDuration,
    onRetrimmed,
}: TimelineEditorProps) {
    const [start, setStart] = useState(startTime);
    const [end, setEnd] = useState(endTime);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const trackRef = useRef<HTMLDivElement>(null);
    const draggingRef = useRef<'start' | 'end' | null>(null);

    const duration = maxDuration || endTime + 30;
    const minClipLength = 5;

    const toPercent = (time: number) => (time / duration) * 100;
    const toTime = (percent: number) => (percent / 100) * duration;

    const formatTime = (seconds: number): string => {
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    const handleMouseDown = (handle: 'start' | 'end') => (e: React.MouseEvent) => {
        e.preventDefault();
        draggingRef.current = handle;
    };

    const handleMouseMove = useCallback(
        (e: MouseEvent) => {
            if (!draggingRef.current || !trackRef.current) return;

            const rect = trackRef.current.getBoundingClientRect();
            const percent = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
            const time = Math.round(toTime(percent) * 10) / 10;

            if (draggingRef.current === 'start') {
                const newStart = Math.max(0, Math.min(time, end - minClipLength));
                setStart(newStart);
            } else {
                const newEnd = Math.min(duration, Math.max(time, start + minClipLength));
                setEnd(newEnd);
            }

            setSuccess(false);
        },
        [start, end, duration]
    );

    const handleMouseUp = useCallback(() => {
        draggingRef.current = null;
    }, []);

    useEffect(() => {
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [handleMouseMove, handleMouseUp]);

    const handleRetrim = async () => {
        setIsSubmitting(true);
        setError(null);
        setSuccess(false);

        try {
            const res = await fetch(`${API_BASE}/api/retrim/${jobId}/${clipId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start_time: start, end_time: end }),
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Re-trim failed');
            }

            const data = await res.json();
            setSuccess(true);
            onRetrimmed?.(`${API_BASE}${data.download_url}`);
        } catch (err: any) {
            setError(err.message || 'Failed to re-trim clip');
        } finally {
            setIsSubmitting(false);
        }
    };

    const hasChanged =
        Math.abs(start - startTime) > 0.5 || Math.abs(end - endTime) > 0.5;

    // Generate waveform bars
    const barCount = 60;
    const bars = Array.from({ length: barCount }, (_, i) => {
        const seed = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
        return 0.15 + (seed - Math.floor(seed)) * 0.85;
    });

    return (
        <div className="mt-4 pt-4" style={{ borderTop: '1px solid rgba(139,92,246,0.1)' }}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-[var(--color-foreground)]/60">
                    ✂️ Timeline Editor
                </span>
                <span className="text-[10px] font-mono text-[var(--color-foreground)]/30">
                    {formatTime(start)} — {formatTime(end)} ({formatTime(end - start)})
                </span>
            </div>

            {/* Track */}
            <div
                ref={trackRef}
                className="relative h-12 rounded-lg overflow-hidden cursor-pointer select-none"
                style={{ background: 'rgba(0,0,0,0.3)' }}
            >
                {/* Waveform bars (background) */}
                <div className="absolute inset-0 flex items-end gap-[1px] px-1 pb-1 pt-1 opacity-30">
                    {bars.map((h, i) => (
                        <div
                            key={i}
                            className="flex-1 rounded-sm"
                            style={{
                                height: `${h * 100}%`,
                                background: 'rgba(139,92,246,0.5)',
                            }}
                        />
                    ))}
                </div>

                {/* Selected range highlight */}
                <div
                    className="absolute top-0 bottom-0 rounded-sm"
                    style={{
                        left: `${toPercent(start)}%`,
                        width: `${toPercent(end) - toPercent(start)}%`,
                        background: 'rgba(139,92,246,0.25)',
                        borderLeft: '2px solid var(--color-primary)',
                        borderRight: '2px solid var(--color-accent)',
                    }}
                />

                {/* Waveform bars (inside selection, brighter) */}
                <div
                    className="absolute top-0 bottom-0 flex items-end gap-[1px] px-1 pb-1 pt-1 overflow-hidden"
                    style={{
                        left: `${toPercent(start)}%`,
                        width: `${toPercent(end) - toPercent(start)}%`,
                    }}
                >
                    {bars.map((h, i) => {
                        const barPercent = (i / barCount) * 100;
                        const selStart = toPercent(start);
                        const selEnd = toPercent(end);
                        const selWidth = selEnd - selStart;
                        const adjustedIndex = Math.floor(((barPercent / 100) * selWidth + selStart) / 100 * barCount);
                        const barHeight = bars[adjustedIndex] || h;
                        return (
                            <div
                                key={i}
                                className="flex-1 rounded-sm"
                                style={{
                                    height: `${barHeight * 100}%`,
                                    background: 'linear-gradient(to top, var(--color-primary), var(--color-accent))',
                                }}
                            />
                        );
                    })}
                </div>

                {/* Start handle */}
                <div
                    className="absolute top-0 bottom-0 w-3 cursor-ew-resize z-10 group/handle flex items-center justify-center"
                    style={{ left: `calc(${toPercent(start)}% - 6px)` }}
                    onMouseDown={handleMouseDown('start')}
                >
                    <div
                        className="w-1 h-6 rounded-full transition-all duration-150 group-hover/handle:h-8 group-hover/handle:w-1.5"
                        style={{ background: 'var(--color-primary)' }}
                    />
                </div>

                {/* End handle */}
                <div
                    className="absolute top-0 bottom-0 w-3 cursor-ew-resize z-10 group/handle flex items-center justify-center"
                    style={{ left: `calc(${toPercent(end)}% - 6px)` }}
                    onMouseDown={handleMouseDown('end')}
                >
                    <div
                        className="w-1 h-6 rounded-full transition-all duration-150 group-hover/handle:h-8 group-hover/handle:w-1.5"
                        style={{ background: 'var(--color-accent)' }}
                    />
                </div>
            </div>

            {/* Time labels below track */}
            <div className="flex justify-between mt-1 text-[9px] font-mono text-[var(--color-foreground)]/20">
                <span>0:00</span>
                <span>{formatTime(duration)}</span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 mt-3">
                <button
                    onClick={handleRetrim}
                    disabled={isSubmitting || !hasChanged}
                    className="px-4 py-2 rounded-lg text-xs font-bold text-white transition-all duration-300 hover:brightness-110 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
                    style={{
                        background:
                            hasChanged
                                ? 'linear-gradient(135deg, var(--color-primary), var(--color-primary-dark))'
                                : 'rgba(139,92,246,0.2)',
                        boxShadow: hasChanged ? '0 2px 12px rgba(139,92,246,0.3)' : 'none',
                    }}
                >
                    {isSubmitting ? (
                        <>
                            <div className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                            Trimming...
                        </>
                    ) : (
                        <>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="6" cy="6" r="3" />
                                <circle cx="6" cy="18" r="3" />
                                <line x1="20" y1="4" x2="8.12" y2="15.88" />
                                <line x1="14.47" y1="14.48" x2="20" y2="20" />
                                <line x1="8.12" y1="8.12" x2="12" y2="12" />
                            </svg>
                            Re-trim
                        </>
                    )}
                </button>

                {success && (
                    <span className="text-xs font-medium animate-fade-in" style={{ color: '#10b981' }}>
                        ✅ Clip updated!
                    </span>
                )}

                {error && (
                    <span className="text-xs font-medium animate-fade-in" style={{ color: '#f87171' }}>
                        ⚠️ {error}
                    </span>
                )}
            </div>
        </div>
    );
}
