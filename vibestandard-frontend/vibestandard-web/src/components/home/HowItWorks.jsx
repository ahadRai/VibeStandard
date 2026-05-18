const STEPS = [
  {
    number: "01",
    title: "Paste your GitHub URL",
    description: "Enter any public GitHub repository URL into the scanner."
  },
  {
    number: "02",
    title: "VibeStandard scans",
    description: "5 analyzers run in parallel across your entire codebase — dependencies, config, security, infra, and observability."
  },
  {
    number: "03",
    title: "Get your verdict",
    description: "Receive a score, grade, and detailed findings list with exact file locations and fix suggestions."
  }
];

export function HowItWorks() {
  return (
    <section className="py-20 px-6" style={{ backgroundColor: 'var(--vs-bg-primary)' }}>
      <div className="max-w-5xl mx-auto">
        <h2
          className="text-center font-sans font-semibold mb-12"
          style={{ fontSize: '32px', color: 'var(--vs-text-primary)', marginBottom: '48px' }}
        >
          How it works
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-4 relative">
          {STEPS.map((step, index) => (
            <div key={index} className="flex flex-col items-center text-center" style={{ padding: '0 16px' }}>
              <div
                className="font-mono font-light"
                style={{
                  fontSize: '48px',
                  color: 'var(--vs-accent)',
                  opacity: 0.4,
                  marginBottom: '16px',
                }}
              >
                {step.number}
              </div>

              <h3
                className="font-sans font-medium"
                style={{ fontSize: '18px', color: 'var(--vs-text-primary)', marginBottom: '8px' }}
              >
                {step.title}
              </h3>

              <p
                className="font-sans font-light"
                style={{ fontSize: '14px', color: 'var(--vs-text-secondary)', lineHeight: '1.6' }}
              >
                {step.description}
              </p>

              {index < STEPS.length - 1 && (
                <div
                  className="hidden md:block absolute"
                  style={{
                    left: `${((index + 1) / 3) * 100}%`,
                    top: '24px',
                    width: '33%',
                    height: '1px',
                    borderTop: '1px dashed var(--vs-border)',
                    transform: 'translateX(-50%)',
                  }}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
