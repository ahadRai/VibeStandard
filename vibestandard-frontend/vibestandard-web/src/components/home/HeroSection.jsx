import { motion } from 'framer-motion';
import { AnimatedBackground } from './AnimatedBackground';
import { SearchBar } from './SearchBar';

export function HeroSection() {
  return (
    <section
      className="relative min-h-screen flex flex-col items-center justify-center"
      style={{ paddingTop: '64px' }}
    >
      <AnimatedBackground />

      <div className="relative z-10 flex flex-col items-center justify-center px-6" style={{ gap: '32px', maxWidth: '100%' }}>
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="font-mono text-[12px] uppercase tracking-[0.15em]"
          style={{
            color: 'var(--vs-accent)',
            border: '1px solid var(--vs-accent-dim)',
            backgroundColor: 'var(--vs-accent-dim)',
            borderRadius: '100px',
            padding: '8px 16px',
          }}
        >
          ◆ Production Readiness Auditor
        </motion.div>

        <motion.h1
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="text-center font-sans font-semibold"
          style={{
            fontSize: 'clamp(36px, 5vw, 64px)',
            color: 'var(--vs-text-primary)',
            lineHeight: '1.1',
            maxWidth: '900px',
          }}
        >
          Is your vibe-coded app
          <br />
          actually <span style={{ color: 'var(--vs-accent)', textShadow: '0 0 40px var(--vs-accent-glow)' }}>production-ready</span>?
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="text-center font-sans font-light"
          style={{
            fontSize: 'clamp(15px, 2vw, 18px)',
            color: 'var(--vs-text-secondary)',
            maxWidth: '560px',
            lineHeight: '1.6',
          }}
        >
          Paste your GitHub repository URL and VibeStandard will scan for
          <br />
          90+ production issues — databases, secrets, security, infra, and observability.
        </motion.p>

        <div style={{ marginTop: '16px' }}>
          <SearchBar />
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="flex flex-wrap justify-center items-center font-sans text-[13px]"
          style={{ 
            color: 'var(--vs-text-muted)',
            gap: '32px',
            marginTop: '8px',
          }}
        >
          <span>✓ 90+ checks</span>
          <span>✓ 5 analyzers</span>
          <span>✓ Free & open source</span>
          <span>✓ No code stored</span>
        </motion.div>
      </div>
    </section>
  );
}
