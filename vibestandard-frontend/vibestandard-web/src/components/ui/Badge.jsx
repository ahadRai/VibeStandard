export function Badge({ label, severity = 'default' }) {
  const severityColors = {
    critical: 'var(--vs-critical)',
    high: 'var(--vs-high)',
    medium: 'var(--vs-medium)',
    low: 'var(--vs-low)',
    success: 'var(--vs-success)',
    default: 'var(--vs-accent)',
  };

  const color = severityColors[severity];

  return (
    <span
      className="inline-block font-mono text-[11px] px-[10px] py-1 rounded-full"
      style={{
        border: `1px solid ${color}`,
        color: color,
        backgroundColor: `${color}15`,
      }}
    >
      {label}
    </span>
  );
}
