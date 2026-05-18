import { motion } from 'framer-motion';

export function GlowButton({ children, onClick, variant = 'primary', size = 'md', disabled = false, loading = false }) {
  const sizeStyles = {
    sm: { padding: '8px 16px', fontSize: '13px' },
    md: { padding: '12px 24px', fontSize: '15px' },
    lg: { padding: '16px 32px', fontSize: '17px' },
  };

  const variantStyles = {
    primary: {
      background: 'var(--vs-accent)',
      color: '#0a1f0d',
      border: 'none',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--vs-accent)',
      border: '1px solid var(--vs-accent)',
    },
  };

  const style = {
    ...sizeStyles[size],
    ...variantStyles[variant],
    borderRadius: '8px',
    fontWeight: '500',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.6 : 1,
    transition: 'all 0.2s',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    outline: 'none',
    fontFamily: 'DM Sans, sans-serif',
    textTransform: 'none',
    letterSpacing: '0',
  };

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || loading}
      whileTap={{ scale: 0.97 }}
      style={style}
      onMouseEnter={(e) => {
        if (variant === 'primary') {
          e.currentTarget.style.filter = 'brightness(1.1)';
        } else {
          e.currentTarget.style.background = 'var(--vs-accent-dim)';
        }
      }}
      onMouseLeave={(e) => {
        if (variant === 'primary') {
          e.currentTarget.style.filter = 'brightness(1)';
        } else {
          e.currentTarget.style.background = 'transparent';
        }
      }}
    >
      {loading ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
          <path d="M21 12a9 9 0 11-6.219-8.56" />
        </svg>
      ) : null}
      {children}
    </motion.button>
  );
}
