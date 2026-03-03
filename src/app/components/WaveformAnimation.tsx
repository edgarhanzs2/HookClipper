'use client';

export default function WaveformAnimation() {
    const barCount = 40;

    return (
        <div className="flex items-center justify-center gap-[3px] h-16 my-6">
            {Array.from({ length: barCount }).map((_, i) => (
                <div
                    key={i}
                    className="rounded-full"
                    style={{
                        width: '4px',
                        background: `linear-gradient(to top, var(--color-primary), var(--color-accent))`,
                        animation: `wave-bar 1.2s ease-in-out infinite`,
                        animationDelay: `${i * 0.05}s`,
                        height: '12px',
                        opacity: 0.6 + Math.random() * 0.4,
                    }}
                />
            ))}
        </div>
    );
}
