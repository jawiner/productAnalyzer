// Applies a business's theme (from business_themes) plus any attribute
// overrides from the <booking-widget> host element as CSS custom properties
// on the widget root node. Every component reads colors via Tailwind's
// primary/secondary/etc classes, which are wired to these variables in
// tailwind.config.js — components never hardcode a client's brand color.

function hexToRgbTriplet(hex) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '');
  if (!m) return null;
  return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
}

// Simple relative-luminance check so foreground text stays legible against
// an arbitrary client brand color, without needing a full color library.
function readableForeground(hex) {
  const rgb = hexToRgbTriplet(hex);
  if (!rgb) return '#ffffff';
  const [r, g, b] = rgb.map((v) => v / 255);
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 0.6 ? '#0f172a' : '#ffffff';
}

/**
 * @param {HTMLElement} rootEl element to set CSS custom properties on
 * @param {object} businessTheme row from business_themes (or null)
 * @param {object} overrides { theme?: 'light'|'dark', primaryColor?, buttonStyle? } from host attributes
 */
export function applyTheme(rootEl, businessTheme, overrides = {}) {
  if (!rootEl) return;
  rootEl.classList.add('booking-widget-root');

  const primary = overrides.primaryColor || businessTheme?.primary_color || '#2563eb';
  const secondary = businessTheme?.secondary_color || '#1e293b';
  const fontFamily = businessTheme?.font_family || 'Inter, system-ui, sans-serif';
  const buttonStyle = overrides.buttonStyle || businessTheme?.button_style || 'rounded';

  rootEl.style.setProperty('--bw-primary', primary);
  rootEl.style.setProperty('--bw-primary-foreground', readableForeground(primary));
  rootEl.style.setProperty('--bw-secondary', secondary);
  rootEl.style.setProperty('--bw-secondary-foreground', readableForeground(secondary));
  rootEl.style.setProperty('--bw-font-family', fontFamily);

  if (overrides.theme === 'dark') {
    rootEl.setAttribute('data-theme', 'dark');
  } else {
    rootEl.removeAttribute('data-theme');
  }
  rootEl.setAttribute('data-button-style', buttonStyle);

  if (businessTheme?.logo_url) {
    rootEl.style.setProperty('--bw-logo-url', `url("${businessTheme.logo_url}")`);
  }
}
