import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ThemeToggle } from '../ui/ThemeToggle';
import logo from '../../assets/logo.png';

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Docs', path: '/docs' },
    { name: 'About', path: '/about' },
  ];

  return (
    <nav
      className="fixed top-0 left-0 right-0 w-full z-50"
      style={{
        height: '64px',
        background: 'rgba(98, 251, 152, 1)',
        boxShadow: scrolled
          ? '0 2px 20px rgba(0,0,0,0.15)'
          : '0 1px 0 rgba(0,0,0,0.1)',
      }}
    >
      <div className="h-full px-6 flex items-center justify-between max-w-7xl mx-auto">
        <Link to="/" className="flex items-center">
          <img src={logo} alt="VibeStandard" style={{ height: '48px', width: 'auto' }} />
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              aria-current={location.pathname === link.path ? 'page' : undefined}
              className="relative text-[#0a1f0d] font-medium text-[15px] hover:text-[#0a1f0d] transition-colors group"
              style={{
                textDecoration: 'none',
              }}
            >
              {link.name}
              <span
                className="absolute left-0 bottom-[-4px] w-full h-[2px] bg-[#0a1f0d] origin-left transition-transform duration-200 scale-x-0 group-hover:scale-x-100"
              />
            </Link>
          ))}

          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="relative text-[#0a1f0d] font-medium text-[15px] flex items-center gap-1.5"
            style={{ textDecoration: 'none' }}
          >
            GitHub
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
          </a>

          <ThemeToggle />
        </div>

        <button
          className="md:hidden flex flex-col gap-1.5 p-2"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          <span className="block w-6 h-0.5 bg-[#0a1f0d] transition-all" />
          <span className="block w-6 h-0.5 bg-[#0a1f0d] transition-all" />
          <span className="block w-6 h-0.5 bg-[#0a1f0d] transition-all" />
        </button>
      </div>

      {mobileMenuOpen && (
        <div
          className="md:hidden absolute top-16 left-0 right-0 px-6 py-4"
          style={{
            background: 'rgba(98, 251, 152, 1)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          }}
        >
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className="block py-3 text-[#0a1f0d] font-medium text-[15px]"
              onClick={() => setMobileMenuOpen(false)}
            >
              {link.name}
            </Link>
          ))}
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="block py-3 text-[#0a1f0d] font-medium text-[15px]"
          >
            GitHub
          </a>
          <div className="pt-3">
            <ThemeToggle />
          </div>
        </div>
      )}
    </nav>
  );
}
