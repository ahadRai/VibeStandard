import { motion } from 'framer-motion';

export function AboutPage() {
  const team = [
    {
      name: 'VibeStandard',
      role: 'Production Readiness Auditor',
      description: 'An open-source tool that scans AI-generated code for 90+ production issues before deployment.',
    },
  ];

  const features = [
    {
      title: '90+ Production Checks',
      description: 'Comprehensive analysis covering dependencies, security, configuration, infrastructure, and observability.',
    },
    {
      title: 'Multi-Ecosystem Support',
      description: 'Native support for Python, Node.js, Java, Go, and Docker with ecosystem-specific rules.',
    },
    {
      title: 'Parallel Analysis',
      description: 'Five specialized analyzers run concurrently for fast, thorough scanning.',
    },
    {
      title: 'Actionable Findings',
      description: 'Every issue includes detailed explanations and concrete fix suggestions.',
    },
    {
      title: 'Smart Scoring',
      description: 'Context-aware scoring with diminishing returns and ecosystem-specific adjustments.',
    },
    {
      title: 'Free to Use',
      description: 'Currently free for all users. Start scanning your repositories today.',
    },
  ];

  const stats = [
    { value: '90+', label: 'Production Checks' },
    { value: '5', label: 'Specialized Analyzers' },
    { value: '6', label: 'Supported Ecosystems' },
    { value: 'Free', label: 'To Use' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full px-6 py-8"
      style={{ maxWidth: '1200px', margin: '0 auto', minHeight: 'calc(100vh - 64px)', paddingTop: '100px' }}
    >
      {/* Hero Section */}
      <div className="mb-16">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-sans font-semibold mb-6"
          style={{ fontSize: '48px', color: 'var(--vs-text-primary)', lineHeight: '1.2' }}
        >
          About VibeStandard
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="font-sans mb-8"
          style={{ fontSize: '20px', color: 'var(--vs-text-secondary)', lineHeight: '1.6', maxWidth: '800px' }}
        >
          VibeStandard was built to solve a critical problem: AI-generated code often works locally but fails in production. 
          We provide the automated checks needed to catch production issues before they reach your users.
        </motion.p>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
          {stats.map((stat, idx) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + idx * 0.1 }}
              className="p-6 rounded-xl text-center"
              style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}
            >
              <div
                className="font-sans font-bold mb-2"
                style={{ fontSize: '36px', color: 'var(--vs-accent)' }}
              >
                {stat.value}
              </div>
              <div
                className="font-sans"
                style={{ fontSize: '14px', color: 'var(--vs-text-muted)' }}
              >
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Mission */}
      <section className="mb-16">
        <h2
          className="font-sans font-semibold mb-6 pb-2 border-b"
          style={{ fontSize: '32px', color: 'var(--vs-accent)', borderColor: 'var(--vs-border)' }}
        >
          Our Mission
        </h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              The Problem
            </h3>
            <p className="font-sans mb-4" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.7' }}>
              Developers are increasingly using AI to generate code. While these tools are powerful, they often produce code 
              that works in development but lacks critical production safeguards: hardcoded secrets, missing error handling, 
              no monitoring, insecure configurations, and more.
            </p>
            <p className="font-sans" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.7' }}>
              Traditional code review processes aren't designed to catch AI-specific patterns, and manual reviews are 
              time-consuming and error-prone.
            </p>
          </div>
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              Our Solution
            </h3>
            <p className="font-sans mb-4" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.7' }}>
              VibeStandard provides automated, ecosystem-aware scanning specifically designed to catch the gap between 
              "it works on my machine" and "it's production-ready." We analyze your code against 90+ production readiness 
              rules across five critical areas.
            </p>
            <p className="font-sans" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.7' }}>
              Every finding includes a clear explanation and actionable fix, so you can quickly address issues and ship 
              with confidence.
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mb-16">
        <h2
          className="font-sans font-semibold mb-8 pb-2 border-b"
          style={{ fontSize: '32px', color: 'var(--vs-accent)', borderColor: 'var(--vs-border)' }}
        >
          Key Features
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="p-6 rounded-xl"
              style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}
            >
              <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '18px', color: 'var(--vs-accent)' }}>
                {feature.title}
              </h3>
              <p className="font-sans" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.6' }}>
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Technology */}
      <section className="mb-16">
        <h2
          className="font-sans font-semibold mb-6 pb-2 border-b"
          style={{ fontSize: '32px', color: 'var(--vs-accent)', borderColor: 'var(--vs-border)' }}
        >
          Technology Stack
        </h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              Core Engine
            </h3>
            <ul className="space-y-2" style={{ color: 'var(--vs-text-secondary)' }}>
              <li className="font-sans">Python 3.13+</li>
              <li className="font-sans">Parallel analyzer execution</li>
              <li className="font-sans">Semgrep integration for security scanning</li>
              <li className="font-sans">YAML-based rule definitions</li>
              <li className="font-sans">Smart deduplication and scoring</li>
            </ul>
          </div>
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              Web Platform
            </h3>
            <ul className="space-y-2" style={{ color: 'var(--vs-text-secondary)' }}>
              <li className="font-sans">FastAPI backend with async support</li>
              <li className="font-sans">React 18 frontend with Framer Motion</li>
              <li className="font-sans">Docker-based deployment</li>
              <li className="font-sans">Background job processing</li>
              <li className="font-sans">Real-time status polling</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Technology */}
      <section className="mb-16">
        <h2
          className="font-sans font-semibold mb-6 pb-2 border-b"
          style={{ fontSize: '32px', color: 'var(--vs-accent)', borderColor: 'var(--vs-border)' }}
        >
          Technology Stack
        </h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              Core Engine
            </h3>
            <ul className="space-y-2" style={{ color: 'var(--vs-text-secondary)' }}>
              <li className="font-sans">Python 3.13+</li>
              <li className="font-sans">Parallel analyzer execution</li>
              <li className="font-sans">Semgrep integration for security scanning</li>
              <li className="font-sans">YAML-based rule definitions</li>
              <li className="font-sans">Smart deduplication and scoring</li>
            </ul>
          </div>
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              Web Platform
            </h3>
            <ul className="space-y-2" style={{ color: 'var(--vs-text-secondary)' }}>
              <li className="font-sans">FastAPI backend with async support</li>
              <li className="font-sans">React 18 frontend with Framer Motion</li>
              <li className="font-sans">Docker-based deployment</li>
              <li className="font-sans">Background job processing</li>
              <li className="font-sans">Real-time status polling</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="mb-16">
        <h2
          className="font-sans font-semibold mb-6 pb-2 border-b"
          style={{ fontSize: '32px', color: 'var(--vs-accent)', borderColor: 'var(--vs-border)' }}
        >
          Team
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {team.map((member, idx) => (
            <motion.div
              key={member.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="p-6 rounded-xl text-center"
              style={{ backgroundColor: 'var(--vs-bg-card)', border: '1px solid var(--vs-border)' }}
            >
              <h3 className="font-sans font-semibold mb-2" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
                {member.name}
              </h3>
              <p className="font-mono text-sm mb-3" style={{ color: 'var(--vs-accent)' }}>
                {member.role}
              </p>
              <p className="font-sans" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.5' }}>
                {member.description}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Contact */}
      <section>
        <h2
          className="font-sans font-semibold mb-6 pb-2 border-b"
          style={{ fontSize: '32px', color: 'var(--vs-accent)', borderColor: 'var(--vs-border)' }}
        >
          Get in Touch
        </h2>
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              Support
            </h3>
            <p className="font-sans mb-4" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.7' }}>
              Need help or have questions about VibeStandard? We're here to assist.
            </p>
          </div>
          <div>
            <h3 className="font-sans font-semibold mb-3" style={{ fontSize: '20px', color: 'var(--vs-text-primary)' }}>
              Feedback
            </h3>
            <p className="font-sans mb-4" style={{ color: 'var(--vs-text-secondary)', lineHeight: '1.7' }}>
              Have suggestions for improvement? We'd love to hear from you.
            </p>
          </div>
        </div>
      </section>
    </motion.div>
  );
}
