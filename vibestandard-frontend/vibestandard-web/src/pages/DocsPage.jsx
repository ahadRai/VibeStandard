import { motion } from 'framer-motion';

export function DocsPage() {
  const sections = [
    {
      title: 'Getting Started',
      content: 'VibeStandard is a production readiness auditor for AI-generated code. It scans GitHub repositories for 90+ production issues across dependencies, configuration, security, infrastructure, and observability.',
    },
    {
      title: 'Quick Start',
      steps: [
        'Navigate to the VibeStandard web application',
        'Paste a public GitHub repository URL into the search bar',
        'Click "Scan Repository"',
        'Wait for the scan to complete (typically 30-60 seconds)',
        'Review the results including score, grade, and detailed findings',
      ],
    },
    {
      title: 'Scoring System',
      content: 'VibeStandard uses a 0-100 scoring system with letter grades:',
      items: [
        { label: 'A (90-100)', description: 'Production Ready - No critical or high severity issues' },
        { label: 'B (75-89)', description: 'Good - Minor issues that should be addressed' },
        { label: 'C (55-74)', description: 'Staging Ready - Medium severity issues present' },
        { label: 'D (30-54)', description: 'Needs Work - Significant issues found' },
        { label: 'F (0-29)', description: 'Test Grade - Critical security or infrastructure issues' },
      ],
    },
    {
      title: 'Vibe Labels',
      items: [
        { label: 'PRODUCTION_READY', description: 'Score ≥90, no critical/high issues, no analyzer errors' },
        { label: 'STAGING_READY', description: 'Score ≥55, no critical issues, ≤1 analyzer error' },
        { label: 'TEST_GRADE', description: 'Anything else - significant issues detected' },
      ],
    },
    {
      title: 'Analyzers',
      content: 'VibeStandard runs five specialized analyzers in parallel:',
      analyzers: [
        {
          name: 'Dependency Analyzer',
          description: 'Checks for outdated, insecure, or misconfigured dependencies across Python, Node.js, Java, and Go ecosystems.',
        },
        {
          name: 'Config Analyzer',
          description: 'Validates configuration files for security best practices, proper environment variable usage, and production readiness.',
        },
        {
          name: 'Security Analyzer',
          description: 'Detects hardcoded secrets, insecure patterns, SQL injection risks, and common vulnerabilities using Semgrep.',
        },
        {
          name: 'Infra Analyzer',
          description: 'Reviews Dockerfiles, docker-compose configurations, and infrastructure setup for production best practices.',
        },
        {
          name: 'Observability Analyzer',
          description: 'Checks for logging, monitoring, health endpoints, error tracking, and other operational requirements.',
        },
      ],
    },
    {
      title: 'Severity Levels',
      items: [
        { label: 'Critical', description: 'Immediate security or stability risk. Must fix before deployment.' },
        { label: 'High', description: 'Significant issue that could cause problems in production.' },
        { label: 'Medium', description: 'Should be addressed, but not blocking for deployment.' },
        { label: 'Low', description: 'Best practice recommendation or minor improvement.' },
      ],
    },
    {
      title: 'Limitations',
      content: 'The web application has the following limitations:',
      items: [
        'Only public GitHub repositories can be scanned',
        'Maximum repository size: 100MB (shallow clone)',
        'Scan results are stored in memory and lost on server restart',
        'Rate limited to 10 scans per minute per IP address',
        'Maximum 5 concurrent scans',
        'Scan timeout: 5 minutes per repository',
      ],
    },
    {
      title: 'Supported Ecosystems',
      items: [
        'Python (requirements.txt, pyproject.toml, setup.py)',
        'Node.js (package.json, yarn.lock, pnpm-lock.yaml)',
        'Java (pom.xml, build.gradle)',
        'Go (go.mod, go.sum)',
        'Docker (Dockerfile, docker-compose.yml)',
        'Generic (language-agnostic checks)',
      ],
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full px-6 py-8"
      style={{ maxWidth: '1200px', margin: '0 auto', minHeight: 'calc(100vh - 64px)', paddingTop: '100px' }}
    >
      <div className="mb-12">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-sans font-semibold mb-4"
          style={{ fontSize: '48px', color: 'var(--vs-text-primary)', lineHeight: '1.2' }}
        >
          Documentation
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="font-sans"
          style={{ fontSize: '18px', color: 'var(--vs-text-secondary)', lineHeight: '1.6', maxWidth: '700px' }}
        >
          Everything you need to know about VibeStandard — from getting started to advanced usage.
        </motion.p>
      </div>

      <div className="space-y-12">
        {sections.map((section, idx) => (
          <motion.section
            key={section.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
          >
            <h2
              className="font-sans font-semibold mb-4 pb-2 border-b"
              style={{ fontSize: '28px', color: 'var(--vs-accent)', borderColor: 'var(--vs-border)' }}
            >
              {section.title}
            </h2>

            {section.content && (
              <p className="font-sans mb-4" style={{ color: 'var(--vs-text-primary)', lineHeight: '1.6', fontSize: '16px' }}>
                {section.content}
              </p>
            )}

            {section.steps && (
              <ol className="space-y-2 ml-6" style={{ listStyleType: 'decimal', color: 'var(--vs-text-primary)' }}>
                {section.steps.map((step, i) => (
                  <li key={i} className="font-sans" style={{ lineHeight: '1.6' }}>
                    {step}
                  </li>
                ))}
              </ol>
            )}

            {section.items && (
              <div className="space-y-3">
                {section.items.map((item, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg"
                    style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}
                  >
                    <div className="font-mono font-semibold mb-1" style={{ color: 'var(--vs-accent)' }}>
                      {item.label}
                    </div>
                    <div className="font-sans" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.5' }}>
                      {item.description}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {section.analyzers && (
              <div className="grid gap-4 md:grid-cols-2">
                {section.analyzers.map((analyzer, i) => (
                  <div
                    key={i}
                    className="p-5 rounded-lg"
                    style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}
                  >
                    <h3 className="font-sans font-semibold mb-2" style={{ color: 'var(--vs-accent)', fontSize: '18px' }}>
                      {analyzer.name}
                    </h3>
                    <p className="font-sans" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.5' }}>
                      {analyzer.description}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {section.code && (
              <pre
                className="p-6 rounded-lg overflow-x-auto"
                style={{
                  backgroundColor: 'var(--vs-bg-secondary)',
                  fontFamily: 'Fira Code, monospace',
                  fontSize: '14px',
                  lineHeight: '1.6',
                  color: 'var(--vs-text-primary)',
                }}
              >
                <code>{section.code}</code>
              </pre>
            )}
          </motion.section>
        ))}
      </div>
    </motion.div>
  );
}
