import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlowButton } from '../ui/GlowButton';

export function ScanResultPanel({ result, onReset, githubUrl }) {
  const [expandedFixes, setExpandedFixes] = useState({});
  const [copied, setCopied] = useState(false);

  const toggleFix = (index) => {
    setExpandedFixes(prev => ({ ...prev, [index]: !prev[index] }));
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadHTMLReport = () => {
    const html = generateHTMLReport(result, githubUrl);
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vibestandard-report-${githubUrl.split('/').slice(-1).join('')}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'A': return 'var(--vs-success)';
      case 'B': return 'var(--vs-accent)';
      case 'C': return 'var(--vs-warning)';
      case 'D': return 'var(--vs-critical)';
      case 'F': return 'var(--vs-critical)';
      default: return 'var(--vs-text-primary)';
    }
  };

  const getVibeLabelColor = (label) => {
    switch (label) {
      case 'PRODUCTION_READY': return 'var(--vs-success)';
      case 'STAGING_READY': return 'var(--vs-warning)';
      case 'TEST_GRADE': return 'var(--vs-critical)';
      default: return 'var(--vs-text-primary)';
    }
  };

  const severityColors = {
    critical: 'var(--vs-critical)',
    high: 'var(--vs-high)',
    medium: 'var(--vs-medium)',
    low: 'var(--vs-low)',
  };

  // Group findings by severity
  const findingsBySeverity = {
    critical: result.findings.filter(f => f.severity === 'critical'),
    high: result.findings.filter(f => f.severity === 'high'),
    medium: result.findings.filter(f => f.severity === 'medium'),
    low: result.findings.filter(f => f.severity === 'low'),
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full px-6 py-8"
      style={{ maxWidth: '1200px', margin: '0 auto' }}
    >
      {/* Result header bar */}
      <div className="flex items-center justify-between mb-8 pb-4 border-b" style={{ borderColor: 'var(--vs-border)' }}>
        <button
          onClick={onReset}
          className="flex items-center gap-2 font-sans font-medium transition-all"
          style={{ color: 'var(--vs-accent)', fontSize: '15px', background: 'none', border: 'none', cursor: 'pointer' }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Scan another repo
        </button>
        <div className="font-mono" style={{ color: 'var(--vs-text-muted)', fontSize: '14px' }}>
          {githubUrl.replace('https://', '')}
        </div>
        <div style={{ color: 'var(--vs-text-muted)', fontSize: '13px' }}>
          Scanned just now
        </div>
      </div>

      {/* Score hero */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Score */}
        <div className="flex flex-col items-center justify-center p-8 rounded-xl" style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
            style={{ fontSize: '72px', fontWeight: 600, color: getGradeColor(result.grade), fontFamily: 'DM Sans, sans-serif' }}
          >
            {result.score}
          </motion.div>
          <div style={{ fontSize: '24px', fontWeight: 500, color: getGradeColor(result.grade), marginTop: '8px' }}>
            Grade: {result.grade}
          </div>
        </div>

        {/* Vibe Label */}
        <div className="flex flex-col items-center justify-center p-8 rounded-xl" style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.3 }}
            className="px-6 py-3 rounded-lg font-bold"
            style={{
              fontSize: '20px',
              backgroundColor: getVibeLabelColor(result.vibe_label) + '20',
              color: getVibeLabelColor(result.vibe_label),
              border: `2px solid ${getVibeLabelColor(result.vibe_label)}`,
            }}
          >
            {result.vibe_label.replace(/_/g, ' ')}
          </motion.div>
        </div>

        {/* Summary counts */}
        <div className="grid grid-cols-2 gap-3">
          {['critical', 'high', 'medium', 'low'].map(severity => (
            <motion.div
              key={severity}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="p-4 rounded-lg text-center"
              style={{ backgroundColor: 'var(--vs-bg-card)', border: `1px solid ${severityColors[severity]}` }}
            >
              <div style={{ fontSize: '28px', fontWeight: 600, color: severityColors[severity] }}>
                {result.summary[severity]}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--vs-text-muted)', textTransform: 'capitalize', marginTop: '4px' }}>
                {severity}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Adjustments applied */}
      {result.adjustments_applied && result.adjustments_applied.length > 0 && (
        <div className="mb-8 p-4 rounded-xl" style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}>
          <h3 className="font-sans font-semibold mb-3" style={{ color: 'var(--vs-text-primary)', fontSize: '16px' }}>
            Score Adjustments
          </h3>
          <div className="space-y-2">
            {result.adjustments_applied.map((adj, idx) => (
              <div key={idx} className="font-mono text-sm" style={{ color: 'var(--vs-text-muted)' }}>
                <span style={{ color: adj.delta > 0 ? 'var(--vs-success)' : 'var(--vs-critical)' }}>
                  {adj.delta > 0 ? '+' : ''}{adj.delta}
                </span>
                {' '}{adj.reason}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analyzer breakdown */}
      <div className="mb-8 p-6 rounded-xl" style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}>
        <h3 className="font-sans font-semibold mb-4" style={{ color: 'var(--vs-text-primary)', fontSize: '18px' }}>
          Analyzer Breakdown
        </h3>
        <div className="space-y-4">
          {Object.entries(result.analyzer_breakdown).map(([analyzer, counts]) => {
            const total = counts.total || 1;
            return (
              <div key={analyzer}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-sans font-medium capitalize" style={{ color: 'var(--vs-text-primary)', fontSize: '14px' }}>
                    {analyzer}
                  </span>
                  <span className="font-mono text-sm" style={{ color: 'var(--vs-text-muted)' }}>
                    {total} findings
                  </span>
                </div>
                <div className="flex h-3 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--vs-bg-secondary)' }}>
                  {counts.critical > 0 && (
                    <div style={{ width: `${(counts.critical / total) * 100}%`, backgroundColor: severityColors.critical }} />
                  )}
                  {counts.high > 0 && (
                    <div style={{ width: `${(counts.high / total) * 100}%`, backgroundColor: severityColors.high }} />
                  )}
                  {counts.medium > 0 && (
                    <div style={{ width: `${(counts.medium / total) * 100}%`, backgroundColor: severityColors.medium }} />
                  )}
                  {counts.low > 0 && (
                    <div style={{ width: `${(counts.low / total) * 100}%`, backgroundColor: severityColors.low }} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Findings list */}
      <div className="mb-8">
        {Object.entries(findingsBySeverity).map(([severity, findings]) => {
          if (findings.length === 0) return null;
          
          return (
            <div key={severity} className="mb-6">
              <h3 className="font-sans font-bold mb-4 flex items-center gap-2" style={{ color: severityColors[severity], fontSize: '18px' }}>
                <span>●</span> {severity.toUpperCase()} ({findings.length})
              </h3>
              <div className="space-y-3">
                {findings.map((finding, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="p-5 rounded-xl"
                    style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}
                  >
                    {/* Top row */}
                    <div className="flex items-center gap-3 mb-3 flex-wrap">
                      <span className="px-2 py-1 rounded font-mono text-xs" style={{ backgroundColor: 'var(--vs-accent-dim)', color: 'var(--vs-accent)' }}>
                        {finding.rule_id}
                      </span>
                      <span className="font-mono text-sm" style={{ color: 'var(--vs-text-muted)' }}>
                        {finding.file}
                      </span>
                      {finding.line && (
                        <span className="font-mono text-xs" style={{ color: 'var(--vs-text-muted)' }}>
                          :{finding.line}
                        </span>
                      )}
                    </div>

                    {/* Message */}
                    <p className="mb-3 font-sans" style={{ color: 'var(--vs-text-primary)', fontSize: '15px', lineHeight: '1.5' }}>
                      {finding.message}
                    </p>

                    {/* Collapsible fix */}
                    <button
                      onClick={() => toggleFix(idx)}
                      className="font-sans text-sm font-medium transition-all"
                      style={{ color: 'var(--vs-accent)', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      {expandedFixes[idx] ? 'Hide fix ▲' : 'Show fix ▼'}
                    </button>
                    <AnimatePresence>
                      {expandedFixes[idx] && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="mt-3 p-4 rounded-lg overflow-hidden"
                          style={{ backgroundColor: 'var(--vs-bg-secondary)', fontFamily: 'Fira Code, monospace', fontSize: '13px', lineHeight: '1.6', color: 'var(--vs-text-primary)' }}
                        >
                          {finding.fix}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Ecosystem tag */}
                    <div className="mt-3">
                      <span className="px-2 py-1 rounded font-mono text-xs" style={{ backgroundColor: 'var(--vs-bg-secondary)', color: 'var(--vs-text-muted)' }}>
                        {finding.ecosystem}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Share / export row */}
      <div className="flex gap-4 flex-wrap">
        <GlowButton onClick={copyToClipboard}>
          {copied ? 'Copied!' : 'Copy JSON'}
        </GlowButton>
        <GlowButton onClick={downloadHTMLReport}>
          Download HTML report
        </GlowButton>
      </div>
    </motion.div>
  );
}

function generateHTMLReport(result, githubUrl) {
  return `
<!DOCTYPE html>
<html>
<head>
  <title>VibeStandard Report - ${githubUrl}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 40px 20px; background: #0a0f0a; color: #e0e0e0; }
    h1 { color: #62fb98; }
    .score { font-size: 72px; font-weight: 600; color: #62fb98; }
    .finding { background: #1a1f1a; padding: 20px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #62fb98; }
    .critical { border-left-color: #ff4444; }
    .high { border-left-color: #ff8800; }
    .medium { border-left-color: #62fb98; }
    .low { border-left-color: #888; }
    pre { background: #0a0f0a; padding: 15px; border-radius: 4px; overflow-x: auto; }
  </style>
</head>
<body>
  <h1>VibeStandard Scan Report</h1>
  <p><strong>Repository:</strong> ${githubUrl}</p>
  <div class="score">${result.score}/100</div>
  <p><strong>Grade:</strong> ${result.grade}</p>
  <p><strong>Status:</strong> ${result.vibe_label}</p>
  <h2>Summary</h2>
  <ul>
    <li>Critical: ${result.summary.critical}</li>
    <li>High: ${result.summary.high}</li>
    <li>Medium: ${result.summary.medium}</li>
    <li>Low: ${result.summary.low}</li>
  </ul>
  <h2>Findings</h2>
  ${result.findings.map(f => `
    <div class="finding ${f.severity}">
      <h3>${f.rule_id} - ${f.name}</h3>
      <p><strong>File:</strong> ${f.file}${f.line ? ':' + f.line : ''}</p>
      <p>${f.message}</p>
      <h4>Fix:</h4>
      <pre>${f.fix}</pre>
    </div>
  `).join('')}
</body>
</html>
  `;
}
