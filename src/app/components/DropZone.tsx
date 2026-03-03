'use client';

import { useState, useRef, useCallback } from 'react';

interface DropZoneProps {
    onFileSelected: (file: File) => void;
}

export default function DropZone({ onFileSelected }: DropZoneProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
    const maxSize = 500 * 1024 * 1024; // 500MB

    const validateFile = useCallback((file: File): boolean => {
        setError(null);
        if (!validTypes.includes(file.type)) {
            setError('Invalid file type. Please upload MP4, MOV, AVI, or WebM.');
            return false;
        }
        if (file.size > maxSize) {
            setError('File too large. Maximum size is 500MB.');
            return false;
        }
        return true;
    }, []);

    const handleFile = useCallback((file: File) => {
        if (validateFile(file)) {
            setSelectedFile(file);
        }
    }, [validateFile]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [handleFile]);

    const handleClick = () => fileInputRef.current?.click();

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
    };

    const formatSize = (bytes: number) => {
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const handleSubmit = () => {
        if (selectedFile) onFileSelected(selectedFile);
    };

    const clearFile = () => {
        setSelectedFile(null);
        setError(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    return (
        <div className="w-full max-w-2xl mx-auto animate-fade-in-up" style={{ animationDelay: '0.3s', opacity: 0 }}>
            {/* Drop Zone */}
            <div
                onClick={handleClick}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
          relative rounded-2xl p-12 cursor-pointer transition-all duration-300 group
          ${isDragging
                        ? 'glass-strong scale-[1.02]'
                        : selectedFile
                            ? 'glass'
                            : 'glass hover:scale-[1.01]'
                    }
        `}
                style={{
                    minHeight: '280px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                {/* Animated border */}
                <div
                    className="absolute inset-0 rounded-2xl opacity-60 group-hover:opacity-100 transition-opacity duration-500"
                    style={{
                        padding: '1.5px',
                        background: isDragging
                            ? 'linear-gradient(135deg, #8b5cf6, #06b6d4, #8b5cf6)'
                            : 'linear-gradient(135deg, rgba(139,92,246,0.4), rgba(6,182,212,0.4), rgba(139,92,246,0.4))',
                        backgroundSize: '200% 200%',
                        animation: 'border-dance 3s ease infinite',
                        WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                        WebkitMaskComposite: 'xor',
                        maskComposite: 'exclude',
                        borderRadius: 'inherit',
                        pointerEvents: 'none',
                    }}
                />

                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp4,.mov,.avi,.webm"
                    className="hidden"
                    onChange={handleInputChange}
                />

                {!selectedFile ? (
                    <>
                        {/* Upload Icon */}
                        <div className={`mb-6 transition-transform duration-300 ${isDragging ? 'scale-110' : 'group-hover:scale-105'}`}>
                            <div className="w-20 h-20 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(139,92,246,0.15)' }}>
                                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-[var(--color-primary-light)]">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
                                    <polyline points="17 8 12 3 7 8" strokeLinecap="round" strokeLinejoin="round" />
                                    <line x1="12" y1="3" x2="12" y2="15" strokeLinecap="round" />
                                </svg>
                            </div>
                        </div>

                        {/* Text */}
                        <p className="text-lg font-semibold text-[var(--color-foreground)] mb-2">
                            {isDragging ? 'Drop your video here!' : 'Drag & drop your video'}
                        </p>
                        <p className="text-sm text-[var(--color-foreground)]/50 mb-4">
                            or click to browse
                        </p>
                        <div className="flex gap-3 flex-wrap justify-center">
                            {['MP4', 'MOV', 'AVI', 'WEBM'].map(fmt => (
                                <span key={fmt} className="text-xs px-3 py-1 rounded-full font-medium" style={{ background: 'rgba(139,92,246,0.1)', color: 'var(--color-primary-light)' }}>
                                    {fmt}
                                </span>
                            ))}
                            <span className="text-xs px-3 py-1 rounded-full font-medium" style={{ background: 'rgba(6,182,212,0.1)', color: 'var(--color-accent-light)' }}>
                                Max 500MB
                            </span>
                        </div>
                    </>
                ) : (
                    /* File Selected State */
                    <div className="text-center animate-fade-in">
                        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{ background: 'rgba(16,185,129,0.15)' }}>
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[var(--color-success)]">
                                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" strokeLinecap="round" strokeLinejoin="round" />
                                <polyline points="14 2 14 8 20 8" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="m10 11 5 3-5 3v-6z" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <p className="text-lg font-semibold text-[var(--color-foreground)] mb-1 truncate max-w-sm">
                            {selectedFile.name}
                        </p>
                        <p className="text-sm text-[var(--color-foreground)]/50 mb-1">
                            {formatSize(selectedFile.size)}
                        </p>
                        <button
                            onClick={(e) => { e.stopPropagation(); clearFile(); }}
                            className="text-xs text-[var(--color-foreground)]/40 hover:text-[var(--color-foreground)]/70 underline mt-1 transition-colors"
                        >
                            Choose a different file
                        </button>
                    </div>
                )}
            </div>

            {/* Error */}
            {error && (
                <div className="mt-4 p-3 rounded-xl text-sm text-center animate-fade-in" style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171' }}>
                    {error}
                </div>
            )}

            {/* Submit Button */}
            {selectedFile && (
                <div className="mt-6 animate-fade-in-up" style={{ animationDelay: '0.1s', opacity: 0 }}>
                    <button
                        onClick={handleSubmit}
                        className="w-full relative overflow-hidden rounded-xl px-8 py-4 text-lg font-bold text-white transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] group"
                        style={{
                            background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
                            boxShadow: '0 0 30px rgba(139,92,246,0.3)',
                        }}
                    >
                        <span className="relative z-10 flex items-center justify-center gap-3">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polygon points="5 3 19 12 5 21 5 3" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            Find Viral Hooks
                        </span>
                        {/* Hover shine */}
                        <div
                            className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                            style={{ background: 'linear-gradient(135deg, rgba(255,255,255,0.1), transparent)' }}
                        />
                    </button>
                </div>
            )}
        </div>
    );
}
