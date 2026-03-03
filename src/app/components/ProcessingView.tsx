'use client';

import WaveformAnimation from './WaveformAnimation';
import ProgressSteps from './ProgressSteps';
import FunFacts from './FunFacts';

interface ProcessingViewProps {
    currentStep: number;
    fileName: string;
}

const steps = [
    { label: 'Uploading', icon: '📤' },
    { label: 'Extracting Audio', icon: '🎵' },
    { label: 'Transcribing', icon: '📝' },
    { label: 'Finding Hooks', icon: '🧠' },
    { label: 'Cutting Clips', icon: '✂️' },
];

const statusMessages = [
    'Uploading your video to the server...',
    'Extracting the audio track with FFmpeg...',
    'AI is listening and transcribing every word...',
    'Analyzing transcript for the most viral moments...',
    'Cutting the best clips from your video...',
];

export default function ProcessingView({ currentStep, fileName }: ProcessingViewProps) {
    return (
        <div className="w-full max-w-2xl mx-auto animate-fade-in-up text-center">
            {/* Header */}
            <div className="mb-10">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass text-xs font-medium text-[var(--color-foreground)]/60 mb-6">
                    <span className="w-2 h-2 rounded-full bg-[var(--color-success)] animate-pulse" />
                    Processing: {fileName}
                </div>
                <h2 className="text-3xl font-bold text-[var(--color-foreground)] mb-2">
                    {steps[currentStep]?.icon} {steps[currentStep]?.label}...
                </h2>
                <p className="text-[var(--color-foreground)]/50 text-sm">
                    {statusMessages[currentStep]}
                </p>
            </div>

            {/* Progress Steps */}
            <ProgressSteps steps={steps} currentStep={currentStep} />

            {/* Waveform Animation */}
            <div className="mt-10">
                <WaveformAnimation />
            </div>

            {/* Spinning loader ring */}
            <div className="flex items-center justify-center mt-6">
                <div
                    className="w-12 h-12 rounded-full border-[3px] border-transparent animate-spin-slow"
                    style={{
                        borderTopColor: 'var(--color-primary)',
                        borderRightColor: 'var(--color-accent)',
                        animationDuration: '2s',
                    }}
                />
            </div>

            {/* Fun Facts */}
            <FunFacts />
        </div>
    );
}
