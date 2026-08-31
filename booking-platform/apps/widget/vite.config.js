import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';

// Standalone dev-mode app shell — used for local development/testing
// (`npm run dev`) and a normal `npm run build`. The embeddable custom
// element bundle is a separate build target, see vite.widget.config.js.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5183,
  },
});
