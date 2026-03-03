'use client';

export default function BlobBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
      {/* Primary blob */}
      <div
        className="absolute animate-morph animate-spin-slow"
        style={{
          width: '600px',
          height: '600px',
          top: '-10%',
          right: '-10%',
          background: 'radial-gradient(circle, rgba(139,92,246,0.15) 0%, rgba(6,182,212,0.05) 50%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      {/* Secondary blob */}
      <div
        className="absolute animate-morph"
        style={{
          width: '500px',
          height: '500px',
          bottom: '-5%',
          left: '-5%',
          background: 'radial-gradient(circle, rgba(6,182,212,0.12) 0%, rgba(139,92,246,0.05) 50%, transparent 70%)',
          filter: 'blur(40px)',
          animationDelay: '-4s',
          animationDuration: '12s',
        }}
      />
      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(139,92,246,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.5) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />
    </div>
  );
}
