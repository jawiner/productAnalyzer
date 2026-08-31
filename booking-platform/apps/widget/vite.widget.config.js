import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';

// Library-mode build that produces a single embeddable script. Including
// this file via <script src=".../widget.js"></script> registers the
// <booking-widget> custom element (see src/widget-entry.jsx), which mounts
// the whole React app into a Shadow DOM wherever it appears in the host
// page's HTML — so hosts just drop in one <script> tag plus the element.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  define: {
    // Library build still reads VITE_SUPABASE_* at build time via
    // import.meta.env, same as the standalone app — Vite inlines these.
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    outDir: 'dist-widget',
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: {
      entry: fileURLToPath(new URL('./src/widget-entry.jsx', import.meta.url)),
      name: 'BookingWidget',
      formats: ['iife'],
      fileName: () => 'widget.js',
    },
    rollupOptions: {
      output: {
        // Single self-contained file: no code-splitting, inline all CSS via
        // the shadow-root injection in widget-entry.jsx rather than a
        // separate .css asset the host page would need to also include.
        inlineDynamicImports: true,
      },
    },
  },
});
