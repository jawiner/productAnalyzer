/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  // Widget mounts inside a Shadow DOM under #booking-widget-root, and also
  // renders standalone under #root during `npm run dev` — cover both.
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // These map to CSS custom properties applied at the widget root
        // (see src/lib/theme.js) so every component derives its look from
        // the business's business_themes row — never hardcode client colors.
        primary: 'var(--bw-primary)',
        'primary-foreground': 'var(--bw-primary-foreground)',
        secondary: 'var(--bw-secondary)',
        'secondary-foreground': 'var(--bw-secondary-foreground)',
        surface: 'var(--bw-surface)',
        'surface-foreground': 'var(--bw-surface-foreground)',
        muted: 'var(--bw-muted)',
        'muted-foreground': 'var(--bw-muted-foreground)',
        border: 'var(--bw-border)',
        destructive: 'var(--bw-destructive)',
        'destructive-foreground': 'var(--bw-destructive-foreground)',
      },
      borderRadius: {
        DEFAULT: 'var(--bw-radius)',
        lg: 'var(--bw-radius-lg)',
        full: '9999px',
      },
      fontFamily: {
        sans: 'var(--bw-font-family)',
      },
    },
  },
  plugins: [],
};
