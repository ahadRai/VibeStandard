import { motion } from 'framer-motion';

const FEATURES = [
  {
    icon: "🗄️",
    title: "Dependency Analyzer",
    description: "Detects H2, SQLite, CVEs, unpinned versions, missing lock files, and dev tools in production.",
    count: "18 checks",
    color: "var(--vs-medium)"
  },
  {
    icon: "⚙️",
    title: "Config Analyzer",
    description: "Catches DEBUG mode, hardcoded secrets, wildcard ALLOWED_HOSTS, and missing environment separation.",
    count: "14 checks",
    color: "var(--vs-high)"
  },
  {
    icon: "🛡️",
    title: "Security Analyzer",
    description: "Finds SQL injection, eval on input, disabled SSL, JWT hardcoded secrets, and missing auth.",
    count: "22 checks",
    color: "var(--vs-critical)"
  },
  {
    icon: "🐳",
    title: "Infra Analyzer",
    description: "Checks Dockerfile, Docker Compose, and CI/CD configs for root containers, missing volumes, and no restart policies.",
    count: "16 checks",
    color: "var(--vs-accent)"
  },
  {
    icon: "📊",
    title: "Observability Analyzer",
    description: "Detects missing health endpoints, no structured logging, absent error tracking, and no graceful shutdown.",
    count: "12 checks",
    color: "var(--vs-success)"
  },
  {
    icon: "⚡",
    title: "90+ Total Checks",
    description: "Every scan covers databases, secrets, security vulnerabilities, infrastructure, and production observability.",
    count: "90+ checks",
    color: "var(--vs-accent)"
  }
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4 },
  },
};

export function FeatureCards() {
  return (
    <section className="py-20 px-6" style={{ backgroundColor: 'var(--vs-bg-primary)' }}>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12" style={{ marginBottom: '48px' }}>
          <h2
            className="font-sans font-semibold mb-3"
            style={{ fontSize: '32px', color: 'var(--vs-text-primary)', marginBottom: '12px' }}
          >
            What VibeStandard detects
          </h2>
          <p
            className="font-sans font-light"
            style={{ fontSize: '16px', color: 'var(--vs-text-secondary)' }}
          >
            Every scan runs 5 specialized analyzers across your entire codebase
          </p>
        </div>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {FEATURES.map((feature, index) => (
            <motion.div
              key={index}
              variants={cardVariants}
              className="rounded-2xl"
              style={{
                background: 'var(--vs-bg-card)',
                border: '1px solid var(--vs-border)',
                padding: '28px',
                transition: 'all 0.3s ease',
                marginBottom: '0',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--vs-border-hover)';
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 12px 40px rgba(98, 251, 152, 0.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--vs-border)';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div className="flex items-start justify-between" style={{ marginBottom: '16px' }}>
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-[20px]"
                  style={{ backgroundColor: 'var(--vs-accent-dim)' }}
                >
                  {feature.icon}
                </div>
                <span
                  className="font-mono text-[11px] px-[10px] py-1 rounded-full"
                  style={{
                    border: `1px solid ${feature.color}`,
                    color: feature.color,
                  }}
                >
                  {feature.count}
                </span>
              </div>

              <h3
                className="font-sans font-medium"
                style={{ fontSize: '18px', color: 'var(--vs-text-primary)', marginBottom: '8px' }}
              >
                {feature.title}
              </h3>

              <p
                className="font-sans font-light"
                style={{ fontSize: '14px', color: 'var(--vs-text-secondary)', lineHeight: '1.6' }}
              >
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
