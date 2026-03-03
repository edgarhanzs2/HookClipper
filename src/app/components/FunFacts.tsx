'use client';

import { useState, useEffect } from 'react';

const facts = [
    { emoji: '🎬', text: 'The first 3 seconds of a video determine 70% of its retention rate.' },
    { emoji: '🔥', text: 'Short-form videos under 60 seconds get 2.5x more engagement than longer content.' },
    { emoji: '🧠', text: 'Humans process visual information 60,000x faster than text.' },
    { emoji: '📱', text: 'TikTok users spend an average of 95 minutes per day on the app.' },
    { emoji: '🎯', text: 'Videos with captions get 40% more views than those without.' },
    { emoji: '⚡', text: 'The best-performing hooks start with a question or bold statement.' },
    { emoji: '🌍', text: 'Over 2 billion short-form videos are watched daily across all platforms.' },
    { emoji: '💡', text: 'Pattern interrupts in the first second can boost watch time by 300%.' },
    { emoji: '📊', text: 'Vertical video ads have a 90% higher completion rate than horizontal.' },
    { emoji: '🎤', text: 'Podcasts repurposed into clips generate 3x more reach than the original episode.' },
];

export default function FunFacts() {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const interval = setInterval(() => {
            setIsVisible(false);
            setTimeout(() => {
                setCurrentIndex(prev => (prev + 1) % facts.length);
                setIsVisible(true);
            }, 400);
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    const fact = facts[currentIndex];

    return (
        <div className="w-full max-w-md mx-auto mt-8">
            <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-foreground)]/30 mb-3 text-center">
                💡 Did you know?
            </p>
            <div
                className="glass rounded-xl px-6 py-4 text-center transition-all duration-400"
                style={{
                    opacity: isVisible ? 1 : 0,
                    transform: isVisible ? 'translateY(0) scale(1)' : 'translateY(8px) scale(0.98)',
                }}
            >
                <span className="text-2xl mb-2 block">{fact.emoji}</span>
                <p className="text-sm leading-relaxed text-[var(--color-foreground)]/70">
                    {fact.text}
                </p>
            </div>
        </div>
    );
}
