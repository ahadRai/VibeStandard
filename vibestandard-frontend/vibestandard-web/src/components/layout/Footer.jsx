export function Footer() {
  return (
    <footer
      className="w-full"
      style={{
        background: 'var(--vs-bg-secondary)',
        borderTop: '1px solid var(--vs-border)',
        height: '72px',
      }}
    >
      <div className="h-full px-6 flex items-center justify-between max-w-7xl mx-auto" style={{ padding: '0 24px' }}>
        <div className="hidden md:block text-[13px]" style={{ color: 'var(--vs-text-muted)', margin: '0' }}>
          © 2025 VibeStandard
        </div>

        <div className="hidden md:block text-[13px]" style={{ color: 'var(--vs-text-muted)', margin: '0' }}>
          Built for developers who ship
        </div>

        <div className="hidden md:flex items-center gap-4 text-[13px]" style={{ gap: '16px' }}>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: 'var(--vs-text-secondary)', margin: '0' }}>
            GitHub
          </a>
          <span style={{ color: 'var(--vs-text-muted)', margin: '0' }}>·</span>
          <a href="/docs" className="hover:underline" style={{ color: 'var(--vs-text-secondary)', margin: '0' }}>
            Docs
          </a>
          <span style={{ color: 'var(--vs-text-muted)', margin: '0' }}>·</span>
          <a href="https://github.com/issues" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: 'var(--vs-text-secondary)', margin: '0' }}>
            Report an issue
          </a>
        </div>

        <div className="md:hidden flex flex-col items-center gap-2 text-[13px]">
          <div style={{ color: 'var(--vs-text-muted)' }}>© 2025 VibeStandard</div>
          <div style={{ color: 'var(--vs-text-muted)' }}>Built for developers who ship</div>
          <div className="flex items-center gap-4">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: 'var(--vs-text-secondary)' }}>
              GitHub
            </a>
            <span style={{ color: 'var(--vs-text-muted)' }}>·</span>
            <a href="/docs" className="hover:underline" style={{ color: 'var(--vs-text-secondary)' }}>
              Docs
            </a>
            <span style={{ color: 'var(--vs-text-muted)' }}>·</span>
            <a href="https://github.com/issues" target="_blank" rel="noopener noreferrer" className="hover:underline" style={{ color: 'var(--vs-text-secondary)' }}>
              Report an issue
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
