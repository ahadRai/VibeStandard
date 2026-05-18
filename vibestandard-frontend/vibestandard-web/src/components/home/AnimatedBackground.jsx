import { useState, useMemo, useEffect } from 'react';

const CODE_FRAGMENTS = [
  "H2 detected",
  "verify=False",
  "DEBUG=True",
  "eval(input)",
  "latest:tag",
  "no HEALTHCHECK",
  "hardcoded secret",
  "no /health route",
  "pickle.loads()",
  "ALLOWED_HOSTS=*",
  "ddl-auto=create-drop",
  "no USER in Docker",
  "SQL injection",
  "no lock file",
  "CORS: *",
  "no structured logging"
];

export function AnimatedBackground({ isLoading = false }) {
  const particles = useMemo(() => {
    return Array.from({ length: 14 }, (_, i) => ({
      id: i,
      text: CODE_FRAGMENTS[Math.floor(Math.random() * CODE_FRAGMENTS.length)],
      left: Math.random() * 100,
      duration: 15 + Math.random() * 20,
      delay: Math.random() * 20,
      fontSize: 11 + Math.random() * 2,
    }));
  }, []);

  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handler = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return (
    <div
      className="absolute inset-0 overflow-hidden pointer-events-none"
      style={{ zIndex: 0 }}
    >
      {/* Layer 1 — Scanning grid */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(98, 251, 152, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(98, 251, 152, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          animation: prefersReducedMotion ? 'none' : `gridDrift 20s infinite linear`,
        }}
      />

      {/* Layer 2 — Floating code fragments */}
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute font-mono whitespace-nowrap"
          style={{
            left: `${particle.left}%`,
            fontSize: `${particle.fontSize}px`,
            color: 'rgba(98, 251, 152, 0.18)',
            animation: prefersReducedMotion ? 'none' : `floatUp ${particle.duration}s infinite linear`,
            animationDelay: `${particle.delay}s`,
          }}
        >
          {particle.text}
        </div>
      ))}

      {/* Layer 3 — Pulse rings */}
      <div className="absolute inset-0 flex items-center justify-center">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="absolute rounded-full border"
            style={{
              width: '200px',
              height: '200px',
              borderColor: 'rgba(98, 251, 152, 0.12)',
              animation: prefersReducedMotion ? 'none' : `pulseRing 4s infinite ease-out`,
              animationDelay: `${i * 1.3}s`,
            }}
          />
        ))}
      </div>

      {/* Layer 4 — Corner accent lines */}
      <div className="absolute top-0 left-0 w-32 h-32">
        <div className="absolute top-4 left-0 w-full h-[1px]" style={{ background: 'rgba(98, 251, 152, 0.15)', transform: 'rotate(15deg)' }} />
        <div className="absolute top-8 left-0 w-full h-[1px]" style={{ background: 'rgba(98, 251, 152, 0.15)', transform: 'rotate(20deg)' }} />
        <div className="absolute top-12 left-0 w-full h-[1px]" style={{ background: 'rgba(98, 251, 152, 0.15)', transform: 'rotate(25deg)' }} />
      </div>
      <div className="absolute bottom-0 right-0 w-32 h-32">
        <div className="absolute bottom-4 right-0 w-full h-[1px]" style={{ background: 'rgba(98, 251, 152, 0.15)', transform: 'rotate(-15deg)' }} />
        <div className="absolute bottom-8 right-0 w-full h-[1px]" style={{ background: 'rgba(98, 251, 152, 0.15)', transform: 'rotate(-20deg)' }} />
        <div className="absolute bottom-12 right-0 w-full h-[1px]" style={{ background: 'rgba(98, 251, 152, 0.15)', transform: 'rotate(-25deg)' }} />
      </div>

      {/* Layer 5 — Scan line sweep */}
      <div
        className="absolute left-0 w-full"
        style={{
          height: '1px',
          background: 'rgba(98, 251, 152, 0.08)',
          boxShadow: '0 0 40px rgba(98, 251, 152, 0.08), 0 0 40px rgba(98, 251, 152, 0.08)',
          animation: prefersReducedMotion ? 'none' : `scanLine ${isLoading ? '3s' : '8s'} infinite linear`,
        }}
      />
    </div>
  );
}
