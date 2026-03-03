'use client';

interface Step {
    label: string;
    icon: string;
}

interface ProgressStepsProps {
    steps: Step[];
    currentStep: number;
}

export default function ProgressSteps({ steps, currentStep }: ProgressStepsProps) {
    return (
        <div className="w-full max-w-lg mx-auto">
            <div className="flex items-center justify-between relative">
                {/* Background line */}
                <div className="absolute top-5 left-0 right-0 h-[2px] bg-[var(--color-border)]" />
                {/* Progress line */}
                <div
                    className="absolute top-5 left-0 h-[2px] transition-all duration-700 ease-out"
                    style={{
                        width: `${(currentStep / (steps.length - 1)) * 100}%`,
                        background: 'linear-gradient(90deg, var(--color-primary), var(--color-accent))',
                        boxShadow: '0 0 12px rgba(139,92,246,0.5)',
                    }}
                />

                {steps.map((step, index) => {
                    const isCompleted = index < currentStep;
                    const isActive = index === currentStep;
                    const isPending = index > currentStep;

                    return (
                        <div key={index} className="flex flex-col items-center relative z-10">
                            {/* Circle */}
                            <div
                                className={`
                  w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold
                  transition-all duration-500
                  ${isActive ? 'animate-progress-pulse' : ''}
                `}
                                style={{
                                    background: isCompleted
                                        ? 'linear-gradient(135deg, var(--color-success), #059669)'
                                        : isActive
                                            ? 'linear-gradient(135deg, var(--color-primary), var(--color-accent))'
                                            : 'var(--color-surface-light)',
                                    border: isPending ? '2px solid var(--color-border)' : 'none',
                                    transform: isActive ? 'scale(1.15)' : 'scale(1)',
                                    boxShadow: isActive ? '0 0 20px rgba(139,92,246,0.4)' : 'none',
                                }}
                            >
                                {isCompleted ? (
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                                        <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                ) : (
                                    <span className="text-base">{step.icon}</span>
                                )}
                            </div>

                            {/* Label */}
                            <p
                                className={`
                  mt-3 text-xs font-medium text-center max-w-[80px] transition-all duration-300
                  ${isActive ? 'text-[var(--color-foreground)]' : 'text-[var(--color-foreground)]/40'}
                `}
                            >
                                {step.label}
                            </p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
