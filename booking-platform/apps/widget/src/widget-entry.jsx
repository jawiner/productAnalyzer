import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { createAppQueryClient } from '@/lib/queryClient';
import { LanguageProvider } from '@/i18n/LanguageContext';
import BookingWidget from '@/components/BookingWidget';
// `?inline` makes Vite return the fully-processed (Tailwind-built) CSS as a
// plain string instead of emitting a separate .css asset — required so the
// whole widget ships as the single `widget.js` file this build target
// produces, with no second <link> tag for the host page to also include.
import widgetCss from '@/index.css?inline';

const TAG_NAME = 'booking-widget';

class BookingWidgetElement extends HTMLElement {
  static get observedAttributes() {
    return ['business-id', 'theme', 'language', 'primary-color', 'button-style'];
  }

  connectedCallback() {
    if (this._mounted) return;
    this._mounted = true;

    // Shadow DOM isolates the widget's styles from the host page (and vice
    // versa) — Tailwind's reset/utilities inside won't leak out, and the
    // host page's CSS can't accidentally clobber the widget's look.
    const shadowRoot = this.attachShadow({ mode: 'open' });

    const styleEl = document.createElement('style');
    styleEl.textContent = widgetCss;
    shadowRoot.appendChild(styleEl);

    const mountEl = document.createElement('div');
    mountEl.id = 'booking-widget-root';
    mountEl.className = 'booking-widget-root';
    shadowRoot.appendChild(mountEl);

    this._shadowRoot = shadowRoot;
    this._mountEl = mountEl;
    this._queryClient = createAppQueryClient();
    this._root = ReactDOM.createRoot(mountEl);

    this._render();
  }

  disconnectedCallback() {
    this._root?.unmount();
    this._mounted = false;
  }

  attributeChangedCallback() {
    if (this._mounted) this._render();
  }

  _render() {
    const businessId = this.getAttribute('business-id');
    const theme = this.getAttribute('theme') || undefined; // 'light' | 'dark'
    const language = this.getAttribute('language') || undefined; // 'en' | 'he'
    const primaryColor = this.getAttribute('primary-color') || undefined;
    const buttonStyle = this.getAttribute('button-style') || undefined;

    if (!businessId) {
      this._mountEl.textContent = 'booking-widget: missing required "business-id" attribute.';
      return;
    }

    // Attribute overrides win over fetched business_theme values — passed
    // through to BookingWidget, which calls applyTheme() with these plus
    // the fetched theme, attributes taking precedence.
    this._root.render(
      React.createElement(
        QueryClientProvider,
        { client: this._queryClient },
        React.createElement(
          LanguageProvider,
          { initialLanguage: language || 'en', rootEl: this._mountEl },
          React.createElement(BookingWidget, {
            businessId,
            rootEl: this._mountEl,
            themeOverrides: { theme, language, primaryColor, buttonStyle },
          })
        )
      )
    );
  }
}

if (!customElements.get(TAG_NAME)) {
  customElements.define(TAG_NAME, BookingWidgetElement);
}
