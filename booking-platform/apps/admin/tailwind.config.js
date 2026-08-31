/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: 'var(--ad-primary)',
        'primary-foreground': 'var(--ad-primary-foreground)',
        secondary: 'var(--ad-secondary)',
        'secondary-foreground': 'var(--ad-secondary-foreground)',
        surface: 'var(--ad-surface)',
        'surface-foreground': 'var(--ad-surface-foreground)',
        muted: 'var(--ad-muted)',
        'muted-foreground': 'var(--ad-muted-foreground)',
        border: 'var(--ad-border)',
        destructive: 'var(--ad-destructive)',
        'destructive-foreground': 'var(--ad-destructive-foreground)',
        success: 'var(--ad-success)',
        warning: 'var(--ad-warning)',
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '0.75rem',
        full: '9999px',
      },
    },
  },
  plugins: [],
};
