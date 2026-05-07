import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      // Proxy all /api/* requests to the Django backend.
      // This avoids CORS and CSRF cookie issues in development.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Preserve cookies (session + csrftoken) across the proxy.
        cookieDomainRewrite: 'localhost',
      },
    },
  },
});
