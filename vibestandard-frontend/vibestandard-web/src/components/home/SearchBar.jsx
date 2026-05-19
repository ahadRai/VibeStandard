import { useState } from 'react';
import { motion } from 'framer-motion';
import { useScan } from '../../hooks/useScan';

export function SearchBar({ isLoading = false, onScanComplete, onScanStart }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [shake, setShake] = useState(false);
  const { scanState, startScan, reset } = useScan();

  const validateGitHubUrl = (input) => {
    const urlPattern = /^https:\/\/github\.com\/[^/]+\/[^/]+/;
    return urlPattern.test(input);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const urlPattern = /^https:\/\/github\.com\/[^/]+\/[^/]+/;
    if (!urlPattern.test(url)) {
      setError('Please enter a valid GitHub repository URL');
      setShake(true);
      setTimeout(() => setShake(false), 500);
      return;
    }

    if (onScanStart) onScanStart(url);
    const result = await startScan(url);
    
    if (result && onScanComplete) {
      onScanComplete(result);
    }
  };

  const isScanning = scanState.status === 'submitting' || scanState.status === 'cloning' || scanState.status === 'scanning';
  const showProgress = isScanning && scanState.progressMessage;
  const showFailure = scanState.status === 'failed';

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut', delay: 0.3 }}
      className="relative"
      style={{ width: 'min(720px, 90vw)' }}
    >
      <form onSubmit={handleSubmit}>
        <div
          className="relative flex items-center rounded-xl border overflow-hidden transition-all"
          style={{
            border: '1px solid var(--vs-border)',
            backgroundColor: 'var(--vs-bg-card)',
          }}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'var(--vs-accent)';
            e.currentTarget.style.boxShadow = '0 0 0 3px var(--vs-accent-glow)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = 'var(--vs-border)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          <div className="pl-4 pr-2 flex items-center" style={{ color: 'var(--vs-text-muted)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          </div>

          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/username/repository"
            aria-label="GitHub repository URL"
            disabled={isLoading}
            className="flex-1 px-2 py-4 outline-none text-base"
            style={{
              color: 'var(--vs-text-primary)',
              fontFamily: 'Fira Code, monospace',
              fontSize: '16px',
              backgroundColor: 'transparent',
            }}
          />

          <button
            type="submit"
            aria-label="Scan repository"
            disabled={isScanning || isLoading}
            className="px-6 font-medium flex items-center gap-2 transition-all duration-200"
            style={{
              height: '48px',
              margin: '8px',
              background: 'var(--vs-accent)',
              color: '#0a0f0a',
              borderRadius: '8px',
              cursor: isScanning || isLoading ? 'not-allowed' : 'pointer',
              opacity: isScanning || isLoading ? 0.6 : 1,
              fontSize: '15px',
              border: 'none',
            }}
            onMouseEnter={(e) => {
              if (!isScanning && !isLoading) {
                e.currentTarget.style.transform = 'scale(1.02)';
                e.currentTarget.style.filter = 'brightness(1.1)';
              }
            }}
            onMouseLeave={(e) => {
              if (!isScanning && !isLoading) {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.filter = 'brightness(1)';
              }
            }}
          >
            {isScanning ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
                <path d="M21 12a9 9 0 11-6.219-8.56" />
              </svg>
            ) : (
              <>
                Scan Repository
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </>
            )}
          </button>
        </div>
      </form>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 font-sans text-[14px]"
          style={{ color: 'var(--vs-critical)' }}
        >
          <div className="flex items-center gap-2">
            <span>✖</span>
            <span>{error}</span>
          </div>
          <div className="ml-6 mt-1" style={{ color: 'var(--vs-text-muted)', fontSize: '13px' }}>
            Example: https://github.com/username/repository
          </div>
        </motion.div>
      )}

      {showProgress && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 font-sans text-[14px]"
          style={{ color: 'var(--vs-accent)' }}
        >
          <div className="flex items-center gap-2">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
              <path d="M21 12a9 9 0 11-6.219-8.56" />
            </svg>
            <span>{scanState.progressMessage}</span>
          </div>
        </motion.div>
      )}

      {showFailure && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 font-sans text-[14px]"
          style={{ color: 'var(--vs-critical)' }}
        >
          <div className="flex items-center gap-2">
            <span>✖</span>
            <span>{scanState.error}</span>
          </div>
          <button
            onClick={reset}
            className="mt-2 px-4 py-2 rounded-lg font-medium transition-all"
            style={{
              background: 'var(--vs-accent)',
              color: '#0a0f0a',
              fontSize: '13px',
              cursor: 'pointer',
              border: 'none',
            }}
          >
            Try again
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}
